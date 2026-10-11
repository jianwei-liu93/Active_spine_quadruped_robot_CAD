"""Run through FreeCAD MCP, before and after implementation (no mocks)."""
def check(doc):
    import math
    assert doc is not None, 'Actual CAD document required'
    bodies=[o for o in doc.Objects if o.TypeId=='PartDesign::Body']
    assert len(bodies)>=18, 'Separate editable spine parts required'
    for b in bodies:
        assert b.Shape.isValid() and b.Shape.Volume>0 and len(b.Shape.Solids)==1,b.Name
        assert any(o.TypeId=='PartDesign::Pad' for o in b.Group),b.Name
    print('CAD acceptance: %s valid single-solid editable bodies' % len(bodies))
