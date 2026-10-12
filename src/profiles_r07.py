"""Exact flat-metal profiles from used native r07 bodies; lead-callable only.

Read-only source geometry; no canonical/companion saves or geometry mutation.
Only genuinely constant-thickness, thin metal parts qualify. Counterbores and
stepped solids fail the full solid-vs-face-extrusion check. DXF entities remain
analytic LINE/ARC/CIRCLE in declared millimetres; no approximation is allowed.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import uuid
from pathlib import Path

TOL_MM=1e-6
VOLUME_REL_TOL=1e-8
MAX_THICKNESS_TO_MIN_SPAN=.35
MATERIALS={'steel','aluminium','aluminum'}
EXCLUDED_TERMS=('purchased','collar','shaft','journal','spacer','grub','bolt','screw','nut envelope','clamp','headed','threaded')


def _used(doc):
    result={}
    for link in doc.Objects:
        if link.TypeId=='App::Link' and link.LinkedObject is not None:
            source=link.LinkedObject
            if source.TypeId=='PartDesign::Body':
                result.setdefault(source.Name,{'body':source,'instances':[]})['instances'].append(link.Name)
    return sorted(result.values(),key=lambda r:str(getattr(r['body'],'PartNumber',r['body'].Name)))


def _selection_reason(source):
    material=str(getattr(source,'MaterialName','')).strip().lower()
    if material not in MATERIALS:return 'material is not candidate steel/aluminium flat stock'
    role=str(getattr(source,'Role','')).upper()
    if role in ('PURCHASED','ENVELOPE','SPRING','CABLE'):return 'explicit excluded role '+role
    text=(source.Name+' '+str(getattr(source,'Process',''))).lower()
    for term in EXCLUDED_TERMS:
        if term in text:return 'process/type exclusion: '+term
    return None


def _profile(source):
    """Select a real planar cap and prove its inward extrusion equals source."""
    import FreeCAD as App, Part
    shape=source.Shape
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:
        raise ValueError('source is not one valid solid')
    candidates=[]
    for index,face in enumerate(shape.Faces,1):
        if 'Plane' not in str(type(face.Surface)):continue
        if not all(w.isClosed() for w in face.Wires):continue
        candidates.append((float(face.Area),index,face))
    for area,index,face in sorted(candidates,key=lambda x:-x[0]):
        if area<=0:continue
        thickness=float(shape.Volume/area)
        u0,u1,v0,v1=face.ParameterRange
        normal=face.normalAt((u0+u1)/2,(v0+v1)/2)
        origin=face.CenterOfMass
        x=App.Vector(1,0,0)
        if abs(normal.dot(x))>.9:x=App.Vector(0,1,0)
        x=x-normal*normal.dot(x);x.normalize();y=normal.cross(x);y.normalize()
        frame=App.Placement(origin,App.Rotation(x,y,normal,'ZXY'))
        planar=face.copy();planar.transformShape(frame.inverse().toMatrix())
        bb=planar.optimalBoundingBox(False,False)
        if bb.ZLength>TOL_MM:continue
        if thickness>min(bb.XLength,bb.YLength)*MAX_THICKNESS_TO_MIN_SPAN:continue
        for sign in (-1,1):
            extrusion=face.extrude(normal*(sign*thickness))
            if extrusion.isNull() or not extrusion.isValid():continue
            missing=float(shape.cut(extrusion).Volume)
            excess=float(extrusion.cut(shape).Volume)
            if max(missing,excess)<=max(1e-9,shape.Volume*VOLUME_REL_TOL):
                return {'face':planar,'face_index':index,'thickness':thickness,
                    'normal':[normal.x,normal.y,normal.z],
                    'origin':[origin.x,origin.y,origin.z],
                    'x_axis':[x.x,x.y,x.z],'y_axis':[y.x,y.y,y.z],
                    'extrusion_sign':sign,'missing_volume_mm3':missing,'excess_volume_mm3':excess,
                    'source_volume_mm3':float(shape.Volume)}
    raise ValueError('no thin planar cap exactly extrudes to the entire solid; stepped/nonplanar/complex parts excluded')


def _entities(face):
    """Keep native outer/inner wires; reject unsupported geometry outright."""
    outer=face.OuterWire
    wires=[outer]+[w for w in face.Wires if not w.isSame(outer)]
    entities=[]
    for wire_index,wire in enumerate(wires):
        layer='OUTER' if wire_index==0 else 'HOLE_%03d'%wire_index
        for edge in wire.Edges:
            curve=edge.Curve;p0=edge.valueAt(edge.FirstParameter);p1=edge.valueAt(edge.LastParameter)
            if 'Line' in str(type(curve)):
                entities.append({'type':'LINE','layer':layer,'start':[p0.x,p0.y],'end':[p1.x,p1.y]})
            elif 'Circle' in str(type(curve)):
                if abs(abs(curve.Axis.z)-1)>TOL_MM:raise ValueError('circular edge not in local profile plane')
                center=curve.Center;radius=float(curve.Radius)
                item={'layer':layer,'center':[center.x,center.y],'radius':radius}
                if abs(edge.Length-2*math.pi*radius)<=TOL_MM:
                    item['type']='CIRCLE'
                else:
                    if curve.Axis.z<0:p0,p1=p1,p0
                    item.update({'type':'ARC','start_angle':math.degrees(math.atan2(p0.y-center.y,p0.x-center.x))%360,
                        'end_angle':math.degrees(math.atan2(p1.y-center.y,p1.x-center.x))%360})
                entities.append(item)
            else:raise ValueError('unsupported native profile curve '+str(type(curve))+'; no approximation exported')
    return entities,len(wires)-1


def _write_dxf(path,entities):
    pairs=[]
    def add(code,value):pairs.extend((str(code),format(value,'.17g') if isinstance(value,float) else str(value)))
    add(0,'SECTION');add(2,'HEADER')
    for name,code,value in [('$ACADVER',1,'AC1015'),('$INSUNITS',70,4),('$MEASUREMENT',70,1),('$LUNITS',70,2),('$LUPREC',70,6)]:
        add(9,name);add(code,value)
    add(0,'ENDSEC');add(0,'SECTION');add(2,'TABLES');add(0,'TABLE');add(2,'LAYER')
    layers=sorted({e['layer'] for e in entities});add(70,len(layers))
    for layer in layers:
        add(0,'LAYER');add(2,layer);add(70,0);add(62,7);add(6,'CONTINUOUS')
    add(0,'ENDTAB');add(0,'ENDSEC');add(0,'SECTION');add(2,'ENTITIES')
    for entity in entities:
        add(0,entity['type']);add(8,entity['layer'])
        if entity['type']=='LINE':
            for prefix,point in [(10,entity['start']),(11,entity['end'])]:
                add(prefix,point[0]);add(prefix+10,point[1]);add(prefix+20,0.)
        else:
            add(10,entity['center'][0]);add(20,entity['center'][1]);add(30,0.);add(40,entity['radius'])
            if entity['type']=='ARC':add(50,entity['start_angle']);add(51,entity['end_angle'])
    add(0,'ENDSEC');add(0,'EOF');path.write_text('\n'.join(pairs)+'\n',encoding='ascii')


def _readback(path,face,entity_count,hole_count):
    """Independent compiled FreeCAD DXF readback into disposable document."""
    import FreeCAD as App, Part, Import
    previous=App.ActiveDocument
    doc=App.newDocument('ProfileDXFCheck_'+uuid.uuid4().hex[:10])
    try:
        Import.readDXF(str(path));doc.recompute()
        edges=[]
        for obj in doc.Objects:
            shape=getattr(obj,'Shape',None)
            if shape is not None and not shape.isNull():edges.extend(shape.Edges)
        if len(edges)!=entity_count:raise ValueError('DXF imported edge/entity count mismatch '+str((len(edges),entity_count)))
        groups=Part.sortEdges(edges)
        wires=[Part.Wire(group) for group in groups]
        if len(wires)!=hole_count+1 or not all(w.isClosed() for w in wires):
            raise ValueError('DXF closed wire/hole topology mismatch')
        shape=Part.makeCompound(wires)
        actual=shape.optimalBoundingBox(False,False);expected=face.optimalBoundingBox(False,False)
        errors={k:abs(getattr(actual,k)-getattr(expected,k)) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')}
        if max(errors.values())>TOL_MM:raise ValueError('DXF geometric bounds mismatch '+str(errors))
        length_error=abs(sum(e.Length for e in edges)-sum(e.Length for e in face.Edges))
        if length_error>TOL_MM:raise ValueError('DXF total contour length mismatch')
        # Rebuild the independent imported closed wires as a face with holes;
        # FaceMakerBullseye determines nesting rather than relying on layer order.
        imported_face=Part.makeFace(wires,'Part::FaceMakerBullseye')
        area_error=abs(float(imported_face.Area-face.Area))
        if area_error>max(TOL_MM,face.Area*1e-8):raise ValueError('DXF profile area/hole geometry mismatch')
        missing_area=float(face.cut(imported_face).Area)
        excess_area=float(imported_face.cut(face).Area)
        if max(missing_area,excess_area)>max(TOL_MM,face.Area*1e-8):
            raise ValueError('DXF contour/hole position symmetric difference mismatch')
        raw=path.read_text(encoding='ascii').splitlines()
        units_ok=any(raw[i:i+4]==['9','$INSUNITS','70','4'] for i in range(len(raw)-3))
        if not units_ok:raise ValueError('DXF millimetre units header absent')
        return {'status':'PASS','reader':'FreeCAD compiled Import.readDXF','edge_count':len(edges),
            'closed_wire_count':len(wires),'hole_count':hole_count,'units':'mm','INSUNITS':4,
            'bounding_box_errors_mm':errors,'contour_length_error_mm':length_error,
            'profile_area_error_mm2':area_error,'missing_profile_area_mm2':missing_area,
            'excess_profile_area_mm2':excess_area,'curved_approximation':'NONE - native lines/arcs/circles'}
    finally:
        App.closeDocument(doc.Name)
        if previous is not None:App.setActiveDocument(previous.Name)


def run(doc,root,only=None,output_dir=None,revision='r07'):
    """Export applicable used metal parts; never recompute/save source document.

    ``only`` bounds probes by source Name. Final lead runs should omit it.
    Source construction/final fixes belong to the lead; rerun after geometry edits.
    """
    revision=str(revision)
    if not re.fullmatch(r'r[0-9]+',revision):raise ValueError('Revision must be r followed by digits')
    root=Path(root).resolve();out=Path(output_dir) if output_dir else root/'exports/profiles'/revision
    out.mkdir(parents=True,exist_ok=True)
    source_file=Path(doc.FileName) if getattr(doc,'FileName','') else None
    before=hashlib.sha256(source_file.read_bytes()).hexdigest() if source_file and source_file.exists() else None
    manifest={'revision':revision,'status':'RUNNING','units':'mm','release_status':'PROVISIONAL - NOT RELEASED FOR FABRICATION',
        'source_file':str(source_file),'source_sha256':before,'selection':'used steel/aluminium thin constant-thickness solids only; purchase/shaft/collar/spring/clamp/fastener exclusions',
        'maximum_thickness_to_minimum_inplane_span':MAX_THICKNESS_TO_MIN_SPAN,
        'profiles':[],'excluded':[],'errors':[]}
    for rec in _used(doc):
        source=rec['body']
        if only is not None and source.Name not in set(only):continue
        reason=_selection_reason(source)
        if reason:manifest['excluded'].append({'source':source.Name,'reason':reason});continue
        try:profile=_profile(source);entities,holes=_entities(profile['face'])
        except Exception as exc:
            manifest['excluded'].append({'source':source.Name,'reason':str(exc)});continue
        pn=str(getattr(source,'PartNumber',source.Name));stem=re.sub('[^A-Za-z0-9._-]+','_',pn)
        path=out/(stem+'.dxf')
        if path.exists() and any(r['path']==str(path) for r in manifest['profiles']):
            raise ValueError('Duplicate manufacturing part ID '+pn)
        _write_dxf(path,entities)
        try:checks=_readback(path,profile['face'],len(entities),holes)
        except Exception as exc:
            manifest['errors'].append({'source':source.Name,'error':str(exc)});continue
        manifest['profiles'].append({'part_number':pn,'source':source.Name,'instances':rec['instances'],
            'material':str(source.MaterialName),'process':str(getattr(source,'Process','')),
            'provenance':'DESIGN_ASSUMPTION source geometry; DERIVED exact profile',
            'thickness_mm':profile['thickness'],'face_index_1based':profile['face_index'],
            'local_plane':{k:profile[k] for k in ('origin','x_axis','y_axis','normal')},
            'solid_equivalence':{k:profile[k] for k in ('source_volume_mm3','missing_volume_mm3','excess_volume_mm3')},
            'entity_count':len(entities),'hole_count':holes,'path':str(path),'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'readback':checks})
    after=hashlib.sha256(source_file.read_bytes()).hexdigest() if source_file and source_file.exists() else None
    if after!=before:raise RuntimeError('Source native file changed during export')
    manifest['source_file_unchanged']=True
    manifest['status']='FAIL' if manifest['errors'] else 'PASS_EXACT_PROFILE_READBACK'
    manifest['profile_count']=len(manifest['profiles'])
    manifest_path=out/('profile_manifest_'+revision+'.json');manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    if manifest['errors']:raise RuntimeError('DXF readback failures: '+str(manifest['errors']))
    return manifest
