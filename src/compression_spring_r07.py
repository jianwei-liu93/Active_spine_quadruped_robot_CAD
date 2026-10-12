"""Compression spring: actual OD4, diameter0.5 wire, 12 turns and closed rings.

Bounded full-torus seam rotations change parameterization only. No dimensions,
wire count, seat positions or physical end geometry are changed. No generic
Shape.fix or STEP normalization is performed.
"""
import math
import hashlib
import json
from pathlib import Path
import time

RADIUS = 1.75
WIRE_RADIUS = .25
TURNS = 12
SEAMS = (43., 11., 23., 37., 61., 17., 29., 53., 71., 89., 101., 131., 0.)
BOUND_TOL = 1e-5
VOLUME_TOL = 1e-6


def _bounds(shape):
    b = shape.optimalBoundingBox(False, False)
    return tuple(getattr(b, key) for key in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))


def validate(shape, length, containment=True):
    """One solid, entire envelope, constituent volume, sampled wire interiors.

    Containment samples inspect all 12 active turns and BOTH full end rings.
    Sampling is finite evidence, not an assertion of exact set equality.
    """
    import FreeCAD as App
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError('Spring is not one valid solid')
    helix_volume = math.pi * WIRE_RADIUS**2 * math.hypot(math.tau*RADIUS*TURNS, length-.5)
    torus_volume = 2*math.pi**2*RADIUS*WIRE_RADIUS**2
    if not helix_volume*.997 <= shape.Volume <= (helix_volume+2*torus_volume)*1.003:
        raise RuntimeError('Spring lost wire or exceeds constituent volume bounds')
    if max(abs(a-b) for a,b in zip(_bounds(shape),(-2.,2.,-2.,2.,0.,length))) > BOUND_TOL:
        raise RuntimeError('Spring does not span exact OD4 and installed seat envelope')
    if containment:
        V = App.Vector
        pitch = (length-.5)/TURNS
        points = []
        for i in range(TURNS*24+1):
            t = math.tau*i/24
            radial = V(math.cos(t),math.sin(t),0)
            tangent = V(-RADIUS*math.sin(t),RADIUS*math.cos(t),pitch/math.tau)
            tangent.normalize()
            other = tangent.cross(radial)
            center = radial*RADIUS + V(0,0,.25+pitch*t/math.tau)
            points.extend(center + direction*(WIRE_RADIUS*.95) for direction in (radial,-radial,other,-other))
        for z in (.25,length-.25):
            for i in range(72):
                t = math.tau*i/72
                radial = V(math.cos(t),math.sin(t),0)
                center = radial*RADIUS + V(0,0,z)
                points.extend(center + direction*(WIRE_RADIUS*.95) for direction in (radial,-radial,V(0,0,1),V(0,0,-1)))
        for i, point in enumerate(points):
            if not shape.isInside(point,1e-6,True):
                raise RuntimeError('Spring missing sampled wire interior '+str(i))
    return shape


def _candidate(length, seam):
    import FreeCAD as App
    import Part
    V=App.Vector
    pitch=(length-.5)/TURNS
    path=Part.Wire(Part.makeHelix(pitch,length-.5,RADIUS).Edges)
    section=Part.Wire([Part.makeCircle(WIRE_RADIUS,V(RADIUS,0,0),V(0,RADIUS,pitch/math.tau))])
    result=path.makePipeShell([section],True,True)
    result.translate(V(0,0,.25))
    for z in (.25,length-.25):
        torus=Part.makeTorus(RADIUS,WIRE_RADIUS,V(0,0,z),V(0,0,1))
        torus.rotate(V(),V(0,0,1),seam)
        result=result.fuse(torus)
    return result.removeSplitter()


def source_hash():
    source=Path(__file__)
    return hashlib.sha256(source.read_bytes()+(source.parent/"spring_normalization_r07.py").read_bytes()).hexdigest()


def shape(length, free_length=None, evidence=None, cache_dir=None):
    """Return complete valid native wire or fail after bounded exact retries.

    No FreeCAD document or object is created or changed.
    """
    import Part
    length=float(length)
    if not math.isfinite(length) or length < 8:
        raise ValueError('Compression spring requires finite length >=8mm')
    start=time.monotonic();failures=[]
    for seam in SEAMS:
        try:
            from spring_normalization_r07 import normalize
            native=validate(normalize(_candidate(length,seam),length),length,False)
            if evidence is not None:
                evidence.update(length_mm=length,seam_deg=seam,volume_mm3=native.Volume,
                                bounds_mm=_bounds(native),failed_candidates=failures,
                                seconds=time.monotonic()-start)
            if cache_dir is not None:
                folder=Path(cache_dir);folder.mkdir(parents=True,exist_ok=True)
                key=length.hex()+"_"+source_hash()
                path=folder/(key+".brep")
                native.exportBrep(str(path))
                record=dict(length_mm=length,length_hex=length.hex(),seam_deg=seam,
                            generator_source_sha256=source_hash(),brep_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            is_valid=native.isValid(),solid_count=len(native.Solids),bounds_mm=_bounds(native),
                            raw_volume_mm3=native.Volume,failed_candidates=failures,seconds=time.monotonic()-start)
                (folder/(key+".json")).write_text(json.dumps(record,indent=2)+"\n")
            return native
        except (RuntimeError,Part.OCCError) as error:
            failures.append({'seam':seam,'error':str(error)})
    raise RuntimeError('Compression spring exhausted exact-geometry candidates: '+repr(failures))
