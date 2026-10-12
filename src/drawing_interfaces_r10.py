"""Bounded critical-interface native diameter construction for r10 drawings.

No geometry, save or export operations. Uses actual source-Body circular
edges and projected circular arcs. Native values are strictly validated.
"""
import json
from pathlib import Path

TOL = 1e-6


def circle_edge(body, diameter, center):
    """Resolve native 1-based edge from radius, local center and source-Z axis."""
    matches = []
    for index, edge in enumerate(body.Shape.Edges, 1):
        curve = edge.Curve
        if 'Circle' not in str(type(curve)) or not hasattr(curve, 'Radius'):
            continue
        if abs(2*curve.Radius-diameter) > TOL:
            continue
        if max(abs(curve.Center[i]-center[i]) for i in range(3)) > TOL:
            continue
        if abs(abs(curve.Axis.z)-1) > TOL:
            continue
        matches.append({'edge': 'Edge'+str(index), 'edge_index_1based': index,
            'diameter_mm': 2*curve.Radius, 'center_source_local_xyz_mm': list(curve.Center),
            'axis_source_local_xyz': list(curve.Axis), 'edge_closed': edge.isClosed(),
            'edge_length_mm': edge.Length})
    if not matches:
        raise ValueError(body.Name+': actual circular source edge missing for '+str((diameter, center)))
    # Deterministic native topology order, including split circular arcs.
    return matches[0]


def interface_specs(doc, root):
    import robot_pose_r03
    from kinematics import spine
    cfg = json.loads((Path(root)/'parameters/assembly_r10.json').read_text())['central_attachment_r10']
    specs = []
    y = cfg['clevis_ear_y_centers_mm'][0]-cfg['clevis_ear_thickness_mm']/2
    for kind in ('fore', 'hind'):
        specs.append({'source': 'TORSO_'+kind.upper()+'_TRANSVERSE_FRAME_r06',
            'key': 'ClevisBore_'+kind, 'diameter': cfg['clevis_pin_bore_mm'],
            'center': (0, 0, 16-y), 'caption': 'central E clevis bore; both ears'})
    stations = spine(0, robot_pose_r03._parameters(doc))
    origin = cfg['frame_origin_world_y_mm']
    seat_z = origin-cfg['lug_half_width_y_mm']
    web_z = seat_z+cfg['bearing_seat_depth_mm']
    for key in ('E1', 'E2'):
        E = stations[key]
        for label, diameter, z in (('LugThroughBore',cfg['lug_through_bore_mm'],web_z),
                                   ('LugBearingSeat',cfg['bearing_seat_diameter_mm'],seat_z)):
            specs.append({'source': 'FRM_LUMBAR_MONOLITHIC_CAGE_r09',
                'key': label+key, 'diameter': diameter, 'center': (E[0], E[1], z),
                'caption': 'central '+key+' '+label})
    groove_z = cfg['pin_length_mm']/2-cfg['pin_groove_center_abs_y_mm']-cfg['pin_groove_width_mm']/2
    for label, diameter, z in (('PinOD',cfg['pin_diameter_mm'],0),
                              ('PinGrooveRoot',cfg['pin_groove_root_diameter_mm'],groove_z)):
        specs.append({'source': 'CENTRAL_E_GROOVED_PIN_r10', 'key': label,
            'diameter': diameter, 'center': (0, 0, z), 'caption': label+'; fits UNVERIFIED'})
    for label, diameter in (('RetainerID',cfg['retainer_id_mm']),('RetainerOD',cfg['retainer_od_mm'])):
        specs.append({'source': 'CENTRAL_E_SPLIT_RETAINER_r10', 'key': label,
            'diameter': diameter, 'center': (0, 0, 0), 'caption': label+'; spring temper/fit UNVERIFIED'})
    return specs


def apply(doc, root):
    """Add ten source-associated diameter sheets; caller saves after verification."""
    import FreeCAD as App
    from drawings_r07 import _dimension, _view_style
    root = Path(root)
    manifest = json.loads((root/'drawings/r10/drawing_manifest_r10.json').read_text())
    if any(r.get('interface_key') for r in manifest['sheets']):
        raise ValueError('Interface sheets already present')
    originals = {r['source']: r for r in manifest['sheets']}
    for spec in interface_specs(doc, root):
        body = doc.getObject(spec['source'])
        source_edge = circle_edge(body, spec['diameter'], spec['center'])
        number = len(manifest['sheets'])+1
        stem = 'R10Drawing_Interface_'+spec['key']
        page = doc.addObject('TechDraw::DrawPage', stem+'_Page')
        template = doc.addObject('TechDraw::DrawSVGTemplate', stem+'_Template')
        template.Template = str(root/'drawings/r10/templates/A4_r10_editable.svg')
        page.Template = template
        doc.recompute()
        fields = dict(template.EditableTexts)
        fields.update(Title=spec['source'],Process='CRITICAL INTERFACE | DESIGN_ASSUMPTION',
            Sheet='INTERFACE '+spec['key'],Scale='See view scale',
            Note='PROVISIONAL. Fits, tolerances, loads and retention capacity UNVERIFIED.',
            Notes1=spec['caption'],Notes2='Actual source circular edge projected normal to its axis.',
            Notes3='Diameter uses native projected circular arc. No arbitrary override.',
            Notes4='Source '+source_edge['edge']+'; regenerate after source geometry edits.',
            Notes5=' ',Notes6=' ',Notes7=' ',Notes8=' ')
        template.EditableTexts = fields
        view = doc.addObject('TechDraw::DrawViewPart',stem+'_View')
        view.Source=[body];view.Direction=App.Vector(*source_edge['axis_source_local_xyz'])
        view.XDirection=App.Vector(1,0,0);view.ScaleType='Custom'
        box=body.Shape.optimalBoundingBox(False,False)
        view.Scale=min(4.,140./max(box.XLength,1e-6),70./max(box.YLength,1e-6))
        view.HardHidden=True;view.SmoothVisible=True
        page.addView(view);view.X=140;view.Y=105;_view_style(view)
        doc.recompute()
        center=view.projectPoint(App.Vector(*spec['center']))-view.projectPoint(box.Center)
        matches=[]
        for index in range(len(view.getVisibleEdges())+len(view.getHiddenEdges())+16):
            try: edge=view.getEdgeByIndex(index)
            except Exception: break
            curve=edge.Curve
            if 'Circle' not in str(type(curve)) or not hasattr(curve,'Radius'): continue
            if abs(2*curve.Radius-spec['diameter'])<TOL and (curve.Center-center).Length<TOL:
                matches.append((index,edge))
        if not matches: raise ValueError('No projected circular arc for '+spec['key'])
        index,edge=matches[0]
        rows=[]
        dim=_dimension(doc,page,view,'Interface_'+spec['key']+'_Diameter','Diameter',
            ['Edge'+str(index)],spec['diameter'],240,155,rows,refs3d=False,caption=spec['caption'])
        if dim.Arbitrary: raise ValueError('Forbidden dimension override')
        rows[0].update(source_object=body.Name,source_edge=source_edge,
            projected_edge_index=index,projected_arc_length_mm=edge.Length,
            projected_center_mm=list(edge.Curve.Center),arbitrary=False)
        old=originals[body.Name]
        record={k:old[k] for k in ('part_number','source','instances','material','process','bbox_extents_xyz_mm')}
        record.update(sheet=number,page=page.Name,scale=view.Scale,dimensions=rows,
            views=[view.Name],errors=[],exports={},critical_fits='UNKNOWN',
            interface_key=spec['key'],native_feature_parameters=[],
            layout='One view bounded within x70..210 y70..140; dimension label at240,155')
        manifest['sheets'].append(record)
    manifest['interface_dimension_count']=10
    manifest['native_dimension_count']=sum(len(r['dimensions']) for r in manifest['sheets'])
    manifest['dimension_count']=manifest['native_dimension_count']
    manifest['sheet_count']=len(manifest['sheets'])
    return manifest
