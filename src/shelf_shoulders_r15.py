"""Native additive shelf-to-case shoulders; source-informed, assumed dimensions.

No file save or connection. Lead alone calls against a private r15 Body.
Retain all old material and features; protect motor and mechanism interfaces.
"""
def apply(body, config):
    from refine_flexor import rect, sketch_face
    from sculpted_frame_r15 import _valid
    cfg = config['sculpted_geometry_r15']['shelf_shoulders']
    x0,x1 = cfg['source_x_abs_bounds_mm']
    y0,y1 = cfg['source_y_bounds_mm']
    intervals = cfg['source_z_intervals_mm']
    if [x0,x1,y0,y1] != [10.,16.,-2.5,2.5] or intervals != [[-9.4,0.],[56.8,66.2]]:
        raise ValueError('Unreviewed shoulder envelope; revise interface and clearance checks')
    doc=body.Document
    before=body.Shape.copy(copyGeom=True,copyMesh=False)
    rows=[]
    doc.openTransaction('r15 continuous shelf-to-motor shoulders')
    try:
        for sign,label in ((1,'Positive'),(-1,'Negative')):
            for side,(za,zb) in zip(('Near','Far'),intervals):
                old=body.Tip
                name='ShelfShoulder'+label+side+'R15'
                if doc.getObject(name):raise ValueError('Shoulder already exists')
                sk=sketch_face(doc,body,name+'Sketch',rect(x0 if sign==1 else -x1,y0,x1-x0,y1-y0),za)
                pad=body.newObject('PartDesign::Pad',name)
                pad.Profile=sk;pad.Length=zb-za
                doc.recompute();_valid(pad)
                if not sk.FullyConstrained:raise RuntimeError('Unconstrained shoulder section')
                old.Visibility=False;sk.Visibility=False
                rows.append({'feature':pad.Name,'length_mm':float(pad.Length),
                             'source_x_bounds_mm':[x0,x1] if sign==1 else [-x1,-x0],
                             'source_y_bounds_mm':[y0,y1],'source_z_bounds_mm':[za,zb]})
        after=body.Shape.copy(copyGeom=True,copyMesh=False)
        removed=before.cut(after).Volume;added=after.cut(before).Volume
        if removed>1e-5 or added<=1e-5:raise RuntimeError('Shoulders must add material only')
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction();doc.recompute();raise
    return {'status':'PASS_LOCAL_GEOMETRY_ONLY','features':rows,
            'baseline_material_removed_mm3':removed,'material_added_mm3':added,
            'volume_before_mm3':before.Volume,'volume_after_mm3':after.Volume,
            'single_valid_solid':True,'source_dimensions':'DESIGN_ASSUMPTION'}
