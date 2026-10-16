"""Actual YZ material sections through four new shoulders; no document writes."""
def compare(old,new):
    import FreeCAD as App,Part
    from section_compare_r15 import _section_properties
    rows=[]
    for x in (-15.5,-13.,-10.5,10.5,13.,15.5):
        for side,(za,zb) in [('near',(-9.4,1.6)),('far',(55.2,66.2))]:
            points=[App.Vector(x,y,z) for y,z in [(-2.5,za),(2.5,za),(2.5,zb),(-2.5,zb),(-2.5,za)]]
            plane=Part.Face(Part.makePolygon(points))
            properties=[]
            for shape in (old,new):
                section=shape.common(plane)
                # Rotation maps source YZ section to XY: X'=Z,Y'=Y,Z'=-X.
                section.rotate(App.Vector(),App.Vector(0,1,0),90.)
                properties.append(_section_properties(section,-x,side,plane='xy'))
            a,b=properties
            if b['area_mm2'] < a['area_mm2']-1e-7:raise RuntimeError('Shoulder loses material')
            rows.append({'source_x_mm':x,'side':side,'source_yz_roi_mm':[-2.5,2.5,za,zb],
                         'r14':a,'r15':b,'area_ratio':b['area_mm2']/a['area_mm2'],
                         'principal_moment_ratios':[v/u for u,v in zip(a['principal_area_moments_mm4'],b['principal_area_moments_mm4'])]})
    return {'status':'PASS_ACTUAL_SHOULDER_SECTIONS_ONLY','records':rows,
            'section_count':len(rows),'minimum_area_ratio':min(r['area_ratio'] for r in rows),
            'minimum_principal_moment_ratio':min(min(r['principal_moment_ratios']) for r in rows),
            'limits':'Local stiffness geometry comparison only; actual loads, anisotropy, buckling, joints, fatigue and strength not qualified.'}
