"""Strict STEP volumes with reproducible installed-OCCT adaptive integration.

Dependencies: C++17 compiler and matching OCCT headers/libraries. Discovery
checks Part's installed tree, FREECAD_OCCT_ROOT, the installed FreeCAD snap,
and standard system prefixes. The helper is compiled under reports/tmp, never
committed as a binary. Missing/incompatible dependencies fail closed.

Primary scalar: GK adaptive Eps1e-10, OnlyClosed=true, IsUseSpan=true.
A bounded Eps1e-12 refinement handles selected-GK convergence failures; the
full coarser variation remains in the numerical margin.
Both GK and Gauss are evaluated at Eps1e-8/1e-10. Precision convergence and
cross-algorithm paired-difference spread contribute an estimated numerical margin.
Large coarse GK estimates trigger unchanged-domain quadrature refinement with
convergence and absolute algorithm-disagreement margins. This is numerical
evidence, not a certified mathematical error bound.
"""
from __future__ import annotations
import ctypes
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EPS_VALUES=(1e-8,1e-10)
CONVERGENCE_REL_TOL=1e-8
REFINEMENT_EPS=1e-12
DOMAIN_REFINEMENT_TRIGGER=2.5e-7
DOMAIN_REFINEMENT_SETTINGS=((8,31),(16,61))
_BACKENDS={}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _installation(occt_root=None):
    try:
        import Part
        part_path=Path(Part.__file__).resolve()
        runtime_version=str(Part.OCC_VERSION)
    except ImportError:
        part_path=None;runtime_version=None
    candidates=[]
    if occt_root:candidates.append(Path(occt_root))
    if os.environ.get('FREECAD_OCCT_ROOT'):candidates.append(Path(os.environ['FREECAD_OCCT_ROOT']))
    if part_path:candidates.append(part_path.parent.parent)
    candidates.extend([Path('/snap/freecad/current/usr'),Path(sys.prefix),Path('/usr/local'),Path('/usr')])
    for prefix in candidates:
        for include in (prefix/'include/opencascade',prefix/'include/oce'):
            header=include/'Standard_Version.hxx'
            if not (include/'BRepGProp.hxx').is_file() or not header.is_file():continue
            version=re.search(r'#define\s+OCC_VERSION_COMPLETE\s+"([^"]+)"',header.read_text())
            if not version:continue
            header_version=version.group(1)
            if runtime_version and header_version!=runtime_version:continue
            for lib in (prefix/'lib',prefix/'lib64',prefix/'lib/x86_64-linux-gnu'):
                if all((lib/n).is_file() for n in ('libTKBRep.so','libTKTopAlgo.so','libTKMath.so')):
                    return include.resolve(),lib.resolve(),runtime_version or header_version
    raise RuntimeError('Matching OCCT development headers/libraries unavailable; checked '+', '.join(map(str,candidates)))


def _build_paths(root,include,lib,occt_version):
    cpp=Path(__file__).with_name('occt_adaptive_volume_r07.cpp')
    if not cpp.is_file():raise RuntimeError('Adaptive volume C++ source is missing: '+str(cpp))
    directory=Path(root).resolve()/'reports/tmp/adaptive_volume_r07';directory.mkdir(parents=True,exist_ok=True)
    header_hash=_sha(include/'BRepGProp.hxx')
    fingerprint=hashlib.sha256((cpp.read_text()+str(include)+str(lib)+occt_version+header_hash).encode()).hexdigest()
    target=directory/('volume_'+fingerprint[:20]+'.so')
    return cpp,directory,target,target.with_suffix('.json'),header_hash


def prepare_backend(root,occt_root=None):
    """Compile from a host Python shell; snap runtimes may lack a compiler."""
    include,lib,occt_version=_installation(occt_root)
    cpp,directory,target,manifest,header_hash=_build_paths(root,include,lib,occt_version)
    compiler=shutil.which(os.environ.get('CXX','c++')) or shutil.which('g++')
    if not compiler:raise RuntimeError('C++17 compiler unavailable. Prepare from the host shell: python src/adaptive_volume_r07.py --prepare ROOT --occt-root /snap/freecad/current/usr')
    args=[compiler,'-std=c++17','-O2','-shared','-fPIC','-I'+str(include),str(cpp),'-L'+str(lib),'-lTKBRep','-lTKTopAlgo','-lTKMath','-Wl,-rpath,'+str(lib)]
    temporary=target.with_suffix('.building.so')
    result=subprocess.run(args+['-o',str(temporary)],capture_output=True,text=True,timeout=120)
    if result.returncode or not temporary.is_file():
        temporary.unlink(missing_ok=True)
        raise RuntimeError('Adaptive volume helper compilation failed: '+(result.stderr or result.stdout)[-4000:])
    temporary.replace(target)
    version=subprocess.run([compiler,'--version'],capture_output=True,text=True,timeout=15)
    metadata={'cpp_source':str(cpp.resolve()),'cpp_sha256':_sha(cpp),'binary':str(target),'binary_sha256':_sha(target),
        'compiler':compiler,'compiler_version':version.stdout.splitlines()[0] if version.stdout else 'unavailable',
        'compile_arguments':args,'occt_header_directory':str(include),'occt_library_directory':str(lib),
        'brepgprop_header_sha256':header_hash,'freecad_occt_version':occt_version,
        'primary_algorithm':'BRepGProp::VolumePropertiesGK,OnlyClosed=true,IsUseSpan=true,CGFlag=false,IFlag=false,SkipShared=false',
        'cross_algorithm':'BRepGProp::VolumeProperties,OnlyClosed=true,SkipShared=false',
        'eps_values':list(EPS_VALUES),'bounded_gk_refinement_eps':REFINEMENT_EPS,'precision_convergence_relative_tolerance':CONVERGENCE_REL_TOL,
        'note':'Numerical margin uses selected GK error estimate, precision convergence and cross-algorithm paired-difference spread; not a certified global bound.'}
    manifest.write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


class _Backend:
    def __init__(self,root):
        include,lib,occt_version=_installation()
        cpp,self.directory,target,manifest,header_hash=_build_paths(root,include,lib,occt_version)
        if not target.is_file() or not manifest.is_file():prepare_backend(root)
        metadata=json.loads(manifest.read_text())
        if metadata.get('cpp_sha256')!=_sha(cpp) or metadata.get('binary_sha256')!=_sha(target) or metadata.get('brepgprop_header_sha256')!=header_hash:
            raise RuntimeError('Adaptive volume cached helper/source/header hash mismatch; rerun host --prepare')
        try:self.library=ctypes.CDLL(str(target))
        except OSError as exc:raise RuntimeError('Cannot load adaptive OCCT helper: '+str(exc)) from exc
        self.library.occt_volume_version.restype=ctypes.c_char_p
        built_version=self.library.occt_volume_version().decode()
        if built_version!=occt_version:
            raise RuntimeError('OCCT helper/FreeCAD version mismatch: '+built_version+' / '+occt_version)
        self.batch=self.library.occt_volume_batch
        self.batch.argtypes=[ctypes.POINTER(ctypes.c_char_p),ctypes.c_size_t,ctypes.c_double,ctypes.c_int,ctypes.POINTER(ctypes.c_double),ctypes.POINTER(ctypes.c_double),ctypes.POINTER(ctypes.c_size_t)]
        self.batch.restype=ctypes.c_int
        self.domain=self.library.occt_volume_domain
        self.domain.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.POINTER(ctypes.c_double),ctypes.POINTER(ctypes.c_double),ctypes.POINTER(ctypes.c_int)]
        self.domain.restype=ctypes.c_int
        self.metadata=dict(metadata,python_measurement_source_sha256=_sha(Path(__file__)),header_version=built_version,freecad_occt_version=occt_version,eps_values=list(EPS_VALUES),bounded_gk_refinement_eps=REFINEMENT_EPS,precision_convergence_relative_tolerance=CONVERGENCE_REL_TOL)
        self.metadata.update(domain_refinement_trigger_relative_error=DOMAIN_REFINEMENT_TRIGGER,domain_refinement_settings=DOMAIN_REFINEMENT_SETTINGS,
            domain_refinement='Original BRepGProp_TFunction boundary parameter intervals; no geometry or topology mutation; full coarse variation and absolute algorithm disagreement retained')
        self.cache={}

    def run_domain(self,path,subdivisions,order,eps=1e-10):
        volume=ctypes.c_double();error=ctypes.c_double();pieces=ctypes.c_int()
        status=self.domain(str(path).encode(),subdivisions,order,eps,ctypes.byref(volume),ctypes.byref(error),ctypes.byref(pieces))
        if status:raise RuntimeError(f'Original-domain volume integration failed code={status}, file={path}')
        return {'algorithm':'original_domain_Gauss_Kronrod','eps':eps,'subdivisions':subdivisions,'order':order,
                'volume_mm3':volume.value,'estimated_relative_integration_error':error.value,'integration_pieces':pieces.value}

    def run_batch(self,paths,eps,algorithm):
        n=len(paths);encoded=[str(p).encode() for p in paths]
        names=(ctypes.c_char_p*n)(*encoded);volumes=(ctypes.c_double*n)();errors=(ctypes.c_double*n)();failed=ctypes.c_size_t()
        status=self.batch(names,n,eps,algorithm,volumes,errors,ctypes.byref(failed))
        if status:raise RuntimeError(f'OCCT adaptive batch failed code={status} index={failed.value} eps={eps} algorithm={algorithm}')
        return list(zip(volumes,errors))


def _backend(root):
    key=str(Path(root).resolve())
    if key not in _BACKENDS:_BACKENDS[key]=_Backend(root)
    return _BACKENDS[key]


def backend_metadata(root):
    return dict(_backend(root).metadata)


def measure_shapes(shapes,root,labels=None):
    """Measure a batch of valid, closed, one-solid BReps; no geometry repair."""
    shapes=list(shapes);labels=list(labels) if labels is not None else [str(i) for i in range(len(shapes))]
    if len(labels)!=len(shapes):raise ValueError('Volume labels/count differ')
    if not shapes:return []
    backend=_backend(root);keys=[];raw=[];pending={}
    for shape,label in zip(shapes,labels):
        if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or not shape.Solids[0].isClosed():
            raise ValueError(str(label)+': adaptive measurement requires a valid closed single solid')
        raw.append(float(shape.Volume))
        with tempfile.NamedTemporaryFile(suffix='.brep',dir=backend.directory,delete=False) as stream:path=Path(stream.name)
        try:
            shape.exportBrep(str(path));key=_sha(path);target=backend.directory/(key+'.brep')
            if target.exists():path.unlink()
            else:path.replace(target)
        finally:path.unlink(missing_ok=True)
        keys.append(key)
        if key not in backend.cache:pending[key]=target
    if pending:
        identifiers=list(pending);paths=[pending[k] for k in identifiers];runs={}
        for algorithm in (0,1):
            for eps in EPS_VALUES:runs[(algorithm,eps)]=backend.run_batch(paths,eps,algorithm)
        refine_indices=[i for i in range(len(identifiers))
                        if abs(runs[(1,EPS_VALUES[1])][i][0]-runs[(1,EPS_VALUES[0])][i][0])/runs[(1,EPS_VALUES[1])][i][0]>CONVERGENCE_REL_TOL]
        refined=dict(zip(refine_indices,backend.run_batch([paths[i] for i in refine_indices],REFINEMENT_EPS,1))) if refine_indices else {}
        for i,key in enumerate(identifiers):
            gauss8,gauss10=runs[(0,EPS_VALUES[0])][i],runs[(0,EPS_VALUES[1])][i]
            gk8,gk10=runs[(1,EPS_VALUES[0])][i],runs[(1,EPS_VALUES[1])][i]
            selected=refined.get(i,gk10)
            volume=selected[0]
            coarse_delta=abs(gk10[0]-gk8[0]);last_delta=abs(selected[0]-gk10[0]) if i in refined else coarse_delta
            gauss_delta=abs(gauss10[0]-gauss8[0]);cross_delta=abs(volume-gauss10[0])
            convergence=last_delta/volume
            if convergence>CONVERGENCE_REL_TOL:
                raise ValueError(f'Adaptive volume fails precision convergence: labels={[str(labels[j]) for j,k in enumerate(keys) if k==key]}, brep={key}, GK8={gk8}, GK10={gk10}, GKrefined={refined.get(i)}, Gauss8={gauss8}, Gauss10={gauss10}, change={convergence} > {CONVERGENCE_REL_TOL}')
            estimated_error=max(gk10[1],selected[1])
            margin=max(estimated_error*volume,coarse_delta,last_delta,gauss_delta)
            measurements=[{'algorithm':name,'eps':eps,'volume_mm3':runs[(algorithm,eps)][i][0],
                           'estimated_relative_integration_error':runs[(algorithm,eps)][i][1]}
                          for algorithm,name in [(0,'adaptive_Gauss'),(1,'adaptive_Gauss_Kronrod_spans')] for eps in EPS_VALUES]
            if i in refined:measurements.append({'algorithm':'adaptive_Gauss_Kronrod_spans','eps':REFINEMENT_EPS,'volume_mm3':volume,'estimated_relative_integration_error':selected[1]})
            selected_algorithm='adaptive_Gauss_Kronrod_spans'
            coarse_error=estimated_error
            if estimated_error>DOMAIN_REFINEMENT_TRIGGER:
                domain_rows=[backend.run_domain(paths[i],subdivisions,order) for subdivisions,order in DOMAIN_REFINEMENT_SETTINGS]
                fine=domain_rows[-1];domain_volume=fine['volume_mm3']
                domain_change=abs(domain_volume-domain_rows[0]['volume_mm3'])
                convergence=domain_change/domain_volume
                if convergence>CONVERGENCE_REL_TOL:
                    raise ValueError(f'Original-domain integration fails convergence for {key}: {convergence} > {CONVERGENCE_REL_TOL}')
                estimated_error=max(r['estimated_relative_integration_error'] for r in domain_rows)
                # New quadrature resolves the coarse estimator plateau; retain
                # observed algorithm discrepancy and every prior precision shift.
                margin=max(coarse_delta,last_delta,gauss_delta,estimated_error*domain_volume,domain_change,
                           *(abs(domain_volume-r['volume_mm3']) for r in measurements))
                volume=domain_volume;cross_delta=abs(volume-gauss10[0]);measurements.extend(domain_rows)
                selected_algorithm='original_domain_Gauss_Kronrod'
            backend.cache[key]={'volume_mm3':volume,'estimated_relative_integration_error':estimated_error,
                'selected_algorithm':selected_algorithm,'coarse_gk_estimated_relative_error':coarse_error,
                'selected_eps':1e-10 if selected_algorithm=='original_domain_Gauss_Kronrod' else REFINEMENT_EPS if i in refined else EPS_VALUES[1],
                'convergence_relative_change':convergence,'coarse_gk_relative_change':coarse_delta/volume,
                'gauss_convergence_relative_change':gauss_delta/volume,'cross_algorithm_relative_difference':cross_delta/volume,'gauss_volume_mm3':gauss10[0],
                'estimated_numerical_margin_mm3':margin,'brep_sha256':key,'measurements':measurements}
    return [dict(backend.cache[key],label=str(label),raw_shape_volume_mm3=value) for key,label,value in zip(keys,labels,raw)]


def measure_shape(shape,root,label='shape'):
    rows=measure_shapes(shape.Solids,root,[str(label)+':'+str(i) for i in range(len(shape.Solids))])
    if not rows:raise ValueError(str(label)+': no physical solids')
    volume=math.fsum(r['volume_mm3'] for r in rows);margin=math.fsum(r['estimated_numerical_margin_mm3'] for r in rows)
    return {'volume_mm3':volume,'gauss_volume_mm3':math.fsum(r['gauss_volume_mm3'] for r in rows),'estimated_numerical_margin_mm3':margin,
            'estimated_relative_integration_error':margin/volume,
            'raw_shape_volume_mm3':float(shape.Volume),'solid_count':len(rows),'solids':rows}


def _box(shape):
    b=shape.optimalBoundingBox(False,False)
    values=[float(getattr(b,k)) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')]
    if not all(math.isfinite(v) for v in values):raise ValueError('Non-finite geometry bounds')
    return values


def compare_measurements(actual,expected,tolerance=1e-6):
    av,ev=actual['volume_mm3'],expected['volume_mm3']
    am,em=actual['estimated_numerical_margin_mm3'],expected['estimated_numerical_margin_mm3']
    if ev<=em:raise ValueError('Native volume numerical margin reaches its volume')
    difference=abs(av-ev)
    paired_algorithm_spread=abs((av-ev)-(actual['gauss_volume_mm3']-expected['gauss_volume_mm3']))
    upper=(difference+am+em+paired_algorithm_spread)/(ev-em)
    return {'volume_relative_error':difference/ev,'paired_algorithm_difference_spread_mm3':paired_algorithm_spread,'estimated_margin_upper_relative_difference':upper,
            'status':'PASS' if upper<=tolerance else 'FAIL'}


def validate_solids(actual_shape,expected_shapes,root,labels=None,volume_rel_tol=1e-6,bbox_abs_tol_mm=1e-5):
    """One-to-one placed-solid gates; every local pair must pass independently."""
    native=[s for shape in expected_shapes for s in shape.Solids];actual=list(actual_shape.Solids)
    labels=list(labels) if labels is not None else ['native_solid_'+str(i) for i in range(len(native))]
    if len(native)!=len(actual) or len(labels)!=len(native) or not native:
        raise ValueError('Placed solid counts/labels differ or are empty')
    nb=[_box(s) for s in native];ab=[_box(s) for s in actual]
    geometric=[]
    for i,box in enumerate(nb):
        choices=[j for j,other in enumerate(ab) if max(abs(x-y) for x,y in zip(box,other))<=bbox_abs_tol_mm]
        if not choices:raise ValueError(labels[i]+': no imported solid matches strict placed bounds')
        geometric.append(choices)
    measured=measure_shapes(native+actual,root,labels+['STEP_solid_'+str(i) for i in range(len(actual))])
    nm=measured[:len(native)];am=measured[len(native):];eligible=[];comparisons={}
    for i,choices in enumerate(geometric):
        good=[]
        for j in choices:
            check=compare_measurements(am[j],nm[i],volume_rel_tol);comparisons[(i,j)]=check
            if check['status']=='PASS':good.append(j)
        if not good:
            best=min(choices,key=lambda j:comparisons[(i,j)]['estimated_margin_upper_relative_difference'])
            check=comparisons[(i,best)]
            raise ValueError(f"{labels[i]}: strict adaptive per-solid volume failed; relative={check['volume_relative_error']:.12g}, with estimated numerical margin={check['estimated_margin_upper_relative_difference']:.12g} > {volume_rel_tol}")
        eligible.append(good)
    assigned={}
    def augment(i,seen):
        for j in eligible[i]:
            if j in seen:continue
            seen.add(j)
            if j not in assigned or augment(assigned[j],seen):assigned[j]=i;return True
        return False
    for i in range(len(native)):
        if not augment(i,set()):raise ValueError('No complete one-to-one placed-solid geometry/volume match')
    mapping={i:j for j,i in assigned.items()};rows=[]
    for i,j in sorted(mapping.items()):
        rows.append({'native_label':labels[i],'step_solid_index':j,'maximum_bbox_absolute_error_mm':max(abs(x-y) for x,y in zip(nb[i],ab[j])),
                     'native_measurement':nm[i],'step_measurement':am[j],**comparisons[(i,j)]})
    nv=math.fsum(r['volume_mm3'] for r in nm);av=math.fsum(r['volume_mm3'] for r in am)
    return {'volume_mm3':av,'expected_volume_mm3':nv,'volume_relative_error':abs(av-nv)/nv,
            'sum_absolute_individual_volume_differences_mm3':math.fsum(abs(am[j]['volume_mm3']-nm[i]['volume_mm3']) for i,j in mapping.items()),
            'maximum_individual_relative_volume_error':max(r['volume_relative_error'] for r in rows),
            'maximum_individual_estimated_margin_upper_relative_difference':max(r['estimated_margin_upper_relative_difference'] for r in rows),
            'raw_import_compound_volume_mm3':float(actual_shape.Volume),
            'raw_native_solid_volume_sum_mm3':math.fsum(float(s.Volume) for s in native),
            'one_to_one_placed_solids':rows,'adaptive_backend':backend_metadata(root)}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',metavar='ROOT',required=True)
    parser.add_argument('--occt-root')
    args=parser.parse_args()
    print(json.dumps(prepare_backend(args.prepare,args.occt_root),indent=2))
