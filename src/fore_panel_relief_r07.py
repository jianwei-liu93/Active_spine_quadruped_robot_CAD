"""Native local panel relief for measured O1 clip sweep; lead-only apply."""
def apply(b):
 import FreeCAD as App
 import cad_common as cc
 d=b.doc;body=d.getObject('Torso_fore').LinkedObject
 if d.getObject('ForeClipReliefR07'):raise ValueError('Relief already installed')
 old=body.Tip
 # Torso(x,y,z) -> source(x,z,16-y). Pocket normal-sourceZ,
 # covering both thin outer panels and no material in the motor interior.
 sk=d.addObject('Sketcher::SketchObject','ForeClipReliefR07_Profile');body.addObject(sk)
 sk.Placement.Base.z=60
 cc.rectangle(sk,34.65,-10,2.35,2.6)
 pk=body.newObject('PartDesign::Pocket','ForeClipReliefR07');pk.Profile=sk;pk.Length=88
 d.recompute();sk.Visibility=False;old.Visibility=False
 if not body.Shape.isValid() or len(body.Shape.Solids)!=1:raise RuntimeError('Fore relief invalid')
 body.Revision='r07';body.Process+='; r07 local O1 clip corner relief X>=34.65,Z<=-7.4'
 return {'native_feature':pk.Name,'shape_valid':True,'dimensions_provenance':'DESIGN_ASSUMPTION; measured motion interference','limits':'Full revised motion verification required'}
