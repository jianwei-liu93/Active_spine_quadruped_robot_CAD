"""Explicit neutral spring trim normalization; never repair an export secretly.

Only the eight tested installed-length definitions use this treatment. At other
poses the generator's valid BRep is retained. See export_repair_r07.md for the
0.20294% kernel integration change and finite geometry-distance evidence.
"""
QUALIFIED_LENGTHS = (24.73863375-7.2, 29.55480766-7.2, 17.5917383, 25.61137956)

def normalize(shape, installed_length):
    # Compression generator receives seat-to-seat coil length (anchors -7.2).
    if not any(abs(installed_length-length)<1e-7 for length in QUALIFIED_LENGTHS):
        return shape
    result=shape.copy()
    if not result.fix(1e-7,1e-9,1e-6) or not result.isValid() or len(result.Solids)!=1:
        raise RuntimeError('Qualified neutral spring normalization failed')
    if abs(result.Volume-shape.Volume)/shape.Volume>.003:
        raise RuntimeError('Neutral spring normalization exceeded recorded volume difference')
    a,b=shape.optimalBoundingBox(False,False),result.optimalBoundingBox(False,False)
    if max(abs(getattr(a,k)-getattr(b,k)) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))>1e-5:
        raise RuntimeError('Neutral spring normalization moved bounding extrema')
    return result
