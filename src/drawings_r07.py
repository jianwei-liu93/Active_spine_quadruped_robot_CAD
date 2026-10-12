"""Lead-callable native TechDraw package for the already-open revision-selected document.

No import-time execution, canonical save, parameter/schema writes or geometry
changes. ``run(doc, root)`` adds only drawings and exports through TechDrawGui.
Dimensions reference native geometry; curved-outline reference extents use
native cosmetic points derived from true curve extrema and must be regenerated
after geometry edits. Measurements are checked to 1e-6 mm. No nominal
value overrides are used. Artifact-operation marking belongs to the caller.
"""
from __future__ import annotations
import itertools
import json
import math
import re
from pathlib import Path

TOL = 1e-6
PREFIX = 'R07Drawing_'  # Compatibility constant for existing r07 callers.


def _revision(revision):
    revision = str(revision)
    if not re.fullmatch(r'r[0-9]+', revision):
        raise ValueError('Revision must be r followed by digits')
    return revision


def _page_prefix(page):
    return page.Name.split('Sheet_', 1)[0]
NS = 'https://www.freecad.org/wiki/index.php?title=Svg_Namespace'


def _stem(text):
    return re.sub('[^A-Za-z0-9_]+', '_', str(text)).strip('_')


def _view_style(view, dimension=False):
    vo = getattr(view, 'ViewObject', None)
    if vo is None:
        return
    for prop, value in (('Font', 'DejaVu Sans'), ('Fontsize', 3.0),
                        ('LineWidth', .35), ('HiddenWidth', .18)):
        if prop in vo.PropertiesList:
            setattr(vo, prop, value)
    if dimension:
        for prop, value in (('Fontsize', 3.0), ('Arrowsize', 1.6)):
            if prop in vo.PropertiesList:
                setattr(vo, prop, value)


def _template(root, revision='r07'):
    """Generate our own corrected modern editable template; preserve input."""
    path = root / 'drawings' / revision / 'templates' / ('A4_'+revision+'_editable.svg')
    path.parent.mkdir(parents=True, exist_ok=True)
    src = (root / 'drawings/templates/A4_candidate.svg').read_text()
    src = re.sub(r'xmlns:freecad="[^"]+"', 'xmlns:freecad="'+NS+'"', src)
    src = re.sub(r'(<text[^>]*>)([^<]*)(</text>)',
                 r'\1<tspan>\2</tspan>\3', src)
    # Short editable secondary notes at the top preserve title-block legibility.
    extra = '<g font-family="DejaVu Sans" font-size="2.5" fill="#222">'
    for i, name in enumerate(('Notes1', 'Notes2', 'Notes3', 'Notes4', 'Notes5', 'Notes6', 'Notes7', 'Notes8')):
        extra += '<text x="12" y="%s" freecad:editable="%s"><tspan> </tspan></text>' % (15+4*i, name)
    extra += '</g>'
    path.write_text(src.replace('</svg>', extra+'</svg>'))
    return path


def _used_bodies(doc, include_purchased=False):
    sources = {}
    for link in doc.Objects:
        if link.TypeId != 'App::Link':
            continue
        body = link.LinkedObject
        if body is None or body.TypeId != 'PartDesign::Body':
            continue
        role = str(getattr(body, 'Role', '')).upper()
        if role in ('PURCHASED', 'ENVELOPE', 'SPRING', 'CABLE'):
            continue
        if not include_purchased and 'purchased' in str(getattr(body, 'Process', '')).lower():
            continue
        sources.setdefault(body.Name, {'body': body, 'instances': []})['instances'].append(link.Name)
    return sorted(sources.values(), key=lambda rec: str(getattr(rec['body'], 'PartNumber', rec['body'].Name)))


def _indexed_vertices(view):
    # HLR visible-list order is NOT getVertexByIndex order in FreeCAD 27.
    # Native index is zero-based; scan the API itself, never zip the two lists.
    result = []
    for index in range(len(view.getVisibleVertexes()) + len(view.getHiddenVertexes()) + 8):
        try:
            vertex = view.getVertexByIndex(index)
            result.append((index, vertex.Point))
        except Exception:
            break
    return result


def _circles(view):
    result = []
    for index in range(len(view.getVisibleEdges())):
        edge = view.getEdgeByIndex(index)
        curve = edge.Curve
        if hasattr(curve, 'Radius') and hasattr(curve, 'Center') and 'Circle' in str(type(curve)):
            # Only full projected circles support diameter and center-pitch refs.
            if abs(edge.Length - 2*math.pi*curve.Radius) < TOL:
                result.append((index, float(curve.Radius), curve.Center))
    return result


def _dimension(doc, page, view, name, kind, refs, expected, x, y, records,
               refs3d=False, caption=None):
    dim = doc.addObject('TechDraw::DrawViewDimension', _page_prefix(page)+name)
    dim.Type = kind
    dim.MeasureType = 'True' if refs3d else 'Projected'
    if refs3d:
        dim.References3D = refs
    else:
        dim.References2D = [(view, tuple(refs))]
    dim.FormatSpec = '%.3f'
    dim.ShowUnits = True
    if caption:
        dim.Caption = caption
    page.addView(dim)
    dim.X, dim.Y = x, y
    _view_style(dim, True)
    doc.recompute()
    actual = float(dim.getRawValue())
    if not math.isfinite(actual) or abs(actual-expected) > TOL:
        doc.removeObject(dim.Name)
        raise ValueError('%s: native %s != geometry %s' % (name, actual, expected))
    record = {'object': dim.Name, 'type': kind, 'expected_mm': expected,
              'measured_mm': actual, 'absolute_error_mm': abs(actual-expected),
              'references': [(o.Name, list(names)) for o, names in refs] if refs3d else list(refs),
              'reference_space': '3D_NATIVE' if refs3d else '2D_NATIVE',
              'provenance': 'DESIGN_ASSUMPTION'}
    records.append(record)
    return dim


def _curve_extrema(source, axis):
    """Locate source edge points at axis extrema, retaining regeneration data."""
    candidates = []
    for edge_index, edge in enumerate(source.Shape.Edges, 1):
        first, last = float(edge.FirstParameter), float(edge.LastParameter)
        params = [first, last]
        curve = edge.Curve
        if hasattr(curve, 'XAxis') and hasattr(curve, 'YAxis') and hasattr(curve, 'Radius'):
            angle = math.atan2(curve.YAxis[axis], curve.XAxis[axis])
            for turn in range(-3, 4):
                for p in (angle+2*math.pi*turn, angle+math.pi+2*math.pi*turn):
                    if first-TOL <= p <= last+TOL:
                        params.append(max(first, min(last, p)))
        elif 'Line' not in str(type(curve)):
            # General curved edge fallback: bracket each sampled local extremum,
            # then refine on the real native parameterized edge, never a mesh.
            n = 128
            grid = [first+(last-first)*i/n for i in range(n+1)]
            values = [edge.valueAt(t)[axis] for t in grid]
            for sign in (-1, 1):
                for i in range(1, n):
                    if sign*values[i] >= sign*values[i-1] and sign*values[i] >= sign*values[i+1]:
                        low, high = grid[i-1], grid[i+1]
                        for unused in range(60):
                            a=low+(high-low)/3; b=high-(high-low)/3
                            if sign*edge.valueAt(a)[axis] < sign*edge.valueAt(b)[axis]: low=a
                            else: high=b
                        params.append((low+high)/2)
        for param in params:
            point=edge.valueAt(param)
            candidates.append({'edge_index_1based':edge_index,'curve_parameter':param,
                               'point_world_mm':[point.x,point.y,point.z], 'point':point})
    return (min(candidates,key=lambda c:c['point'][axis]),
            max(candidates,key=lambda c:c['point'][axis]))


def _derived_extent(doc, page, source, view, axis, expected, x, y, records):
    import TechDraw
    axis_index='xyz'.index(axis)
    low,high=_curve_extrema(source,axis_index)
    span=high['point'][axis_index]-low['point'][axis_index]
    if abs(span-expected)>TOL:
        raise ValueError(source.Name+': native curve extrema disagree with exact bounding box')
    center=source.Shape.optimalBoundingBox(False,False).Center
    projected_center=view.projectPoint(center)
    points=[(view.projectPoint(rec['point'])-projected_center)*view.Scale for rec in (low,high)]
    local_axis=0 if axis == ('y' if view.Label.endswith('YZ') else 'x') else 1
    kind='DistanceX' if local_axis==0 else 'DistanceY'
    dim=TechDraw.makeDistanceDim(view,kind,points[0],points[1])
    dim.Label=_page_prefix(page)+source.Name+'_'+axis+'_REF_Extent'
    # makeDistanceDim already inserts the native dimension in its parent page.
    dim.FormatSpec='%.3f';dim.ShowUnits=True
    dim.Caption='REF overall extent'
    dim.addProperty('App::PropertyString','ReferenceNote','Drawing provenance')
    dim.ReferenceNote='REF overall extent; regenerate drawing after model edits'
    dim.X=x;dim.Y=y;_view_style(dim,True);doc.recompute()
    actual=float(dim.getRawValue())
    if not math.isfinite(actual) or abs(actual-expected)>TOL:
        doc.removeObject(dim.Name)
        raise ValueError(source.Name+': derived extent native measurement mismatch')
    records.append({'object':dim.Name,'type':kind,'expected_mm':expected,'measured_mm':actual,
        'absolute_error_mm':abs(actual-expected),'reference_space':'2D_NATIVE_COSMETIC_CURVE_EXTREMA',
        'references':[(o.Name,list(names)) for o,names in dim.References2D],
        'provenance':'DERIVED from DESIGN_ASSUMPTION native model',
        'source':source.Name,'source_associations':[{k:v for k,v in rec.items() if k!='point'} for rec in (low,high)],
        'automatic_model_edit_propagation':False,
        'note':'REF overall extent; regenerate drawing after model edits'})
    return dim


def _extent(doc, page, source, view, axis, expected, x, y, records):
    """True source XYZ extents: actual vertices, projected vertices, full circles."""
    coord = 'xyz'.index(axis)
    native = [(i+1, vertex.Point) for i, vertex in enumerate(source.Shape.Vertexes)]
    if native:
        lo = min(native, key=lambda item: item[1][coord])
        hi = max(native, key=lambda item: item[1][coord])
        if abs(hi[1][coord]-lo[1][coord]-expected) <= TOL:
            try:
                return _dimension(doc, page, view, source.Name+'_'+axis+'Extent',
                    'Distance'+axis.upper(), [(source, ('Vertex'+str(lo[0]), 'Vertex'+str(hi[0])))],
                    expected, x, y, records, True)
            except ValueError:
                pass
    # View's XDirection selects global +X (XY/XZ) or +Y (YZ), and the
    # secondary projected axis is +Y/+Z, respectively. Reflection is immaterial.
    local_axis = 0 if axis == ('y' if view.Label.endswith('YZ') else 'x') else 1
    vertices = _indexed_vertices(view)
    if vertices:
        lo = min(vertices, key=lambda item: item[1][local_axis])
        hi = max(vertices, key=lambda item: item[1][local_axis])
        span = hi[1][local_axis]-lo[1][local_axis]
        if abs(span-expected) <= TOL:
            try:
                return _dimension(doc, page, view, source.Name+'_'+axis+'Extent',
                    'DistanceX' if local_axis == 0 else 'DistanceY',
                    ['Vertex'+str(lo[0]), 'Vertex'+str(hi[0])], expected, x, y, records)
            except ValueError:
                pass
    for edge, radius, center in _circles(view):
        if abs(radius*2-expected) <= TOL:
            return _dimension(doc, page, view, source.Name+'_'+axis+'CircularExtent',
                'Diameter', ['Edge'+str(edge)], expected, x, y, records,
                caption=axis.upper()+' envelope')
    return _derived_extent(doc,page,source,view,axis,expected,x,y,records)


def _annotation(doc, page, name, lines, x, y, size=2.6):
    obj = doc.addObject('TechDraw::DrawViewAnnotation', _page_prefix(page)+name)
    obj.Text = lines
    obj.TextSize = size
    page.addView(obj)
    obj.X, obj.Y = x, y
    _view_style(obj)
    return obj


def _native_parameters(body):
    rows = []
    for feature in body.Group:
        item = {'object': feature.Name, 'type': feature.TypeId}
        for prop in ('Length', 'Length2', 'Radius', 'Angle', 'Reversed', 'Type'):
            if prop in feature.PropertiesList:
                value = getattr(feature, prop)
                item[prop] = float(value.Value) if hasattr(value, 'Value') else str(value)
        if feature.TypeId == 'Sketcher::SketchObject':
            item['dimensional_constraints'] = [
                {'type': c.Type, 'value': float(c.Value)} for c in feature.Constraints
                if c.Type in ('Distance','DistanceX','DistanceY','Radius','Diameter','Angle')]
        if len(item) > 2:
            rows.append(item)
    return rows


def run(doc, root, export=True, include_purchased=False, strict=True, only=None, revision='r07'):
    """Create editable sheets, export each SVG/PDF, write detailed JSON manifest.

    Call via lead-owned FreeCAD GUI. ``export=False`` permits isolated CLI checks.
    ``only`` bounds probes by source Name. Repeat calls replace only this module's
    revision-prefixed drawing objects. Pass revision='r08' for isolated outputs.
    Does not save the document. Missing genuine extent
    references fail the strict package gate, preserving diagnostics and pages.
    """
    import FreeCAD as App
    root = Path(root).resolve()
    revision = _revision(revision)
    prefix = revision.upper()+'Drawing_'
    doc.recompute()
    selected = _used_bodies(doc, include_purchased)
    if only is not None:
        selected = [rec for rec in selected if rec['body'].Name in set(only)]
    if not selected:
        raise ValueError('No used manufactured native PartDesign bodies selected')
    for obj in reversed(doc.Objects):
        if obj.Name.startswith(prefix) or obj.Label.startswith(prefix):
            doc.removeObject(obj.Name)
    template_path = _template(root, revision)
    out = root / 'drawings' / revision
    out.mkdir(parents=True, exist_ok=True)
    manifest = {'revision': revision, 'units': 'mm', 'status': 'RUNNING',
        'release_status': 'PROVISIONAL - NOT RELEASED FOR FABRICATION',
        'selection': 'unique App::Link-used PartDesign::Body definitions; explicitly purchased process excluded unless requested',
        'extent_tolerance_mm': TOL, 'sheets': [], 'errors': []}
    for sheet, rec in enumerate(selected, 1):
        body = rec['body'];pn = str(getattr(body, 'PartNumber', body.Name))
        box = body.Shape.optimalBoundingBox(False, False)
        extent = (float(box.XLength), float(box.YLength), float(box.ZLength))
        iso_width = (extent[0]+extent[1])/math.sqrt(2)
        iso_height = (extent[0]+extent[1]+2*extent[2])/math.sqrt(6)
        scale = min(2., 76./max(extent[0], extent[1], 1e-6), 47./max(extent[1], extent[2], 1e-6),
                    76./max(iso_width, 1e-6), 47./max(iso_height, 1e-6))
        # Always choose a standard scale that fits all four reserved view cells.
        scale = max([n for n in (2.,1.,.5,.25,.1,.05,.02,.01) if n <= scale] or [.005])
        page = doc.addObject('TechDraw::DrawPage', prefix+'Sheet_%03d'%sheet)
        template = doc.addObject('TechDraw::DrawSVGTemplate', prefix+'Template_%03d'%sheet)
        template.Template = str(template_path)
        page.Template = template  # Must precede addView on FreeCAD 27.
        doc.recompute()
        fields = dict(template.EditableTexts)
        expected_fields = {'Title','Process','Sheet','Scale','Note','Notes1','Notes2','Notes3','Notes4','Notes5','Notes6','Notes7','Notes8'}
        if not expected_fields.issubset(fields):
            raise RuntimeError('Template editable fields unavailable: '+str(fields))
        process = str(getattr(body, 'Process', 'Process unresolved'))
        notes = [process[i:i+125] for i in range(0, min(len(process), 375), 125)]
        fields.update({'Title': pn[:110], 'Process': str(getattr(body,'MaterialName','UNRESOLVED'))+' | '+str(getattr(body,'Role','CUSTOM')),
            'Sheet': 'SHEET %03d / %03d'%(sheet,len(selected)), 'Scale': 'SCALE '+str(scale)+':1',
            'Note': 'All dimensions DESIGN_ASSUMPTION. Validate bores, fits, threads and loads. Do not scale.',
            'Notes1': 'SOURCE '+body.Name+' | orthographic XY / XZ / YZ | dimensions mm',
            'Notes2': notes[0] if notes else 'Process unresolved',
            'Notes3': notes[1] if len(notes)>1 else 'Critical fits UNKNOWN. Finish and inspect bores; no tolerance or fit release.',
            'Notes4': notes[2] if len(notes)>2 else 'PROVISIONAL. REF extents: regenerate drawing after model edits. Critical fits UNKNOWN.'})
        parameters = _native_parameters(body)
        summary = []
        for parameter in parameters:
            if 'Length' in parameter:
                summary.append(parameter['object'].replace(body.Name+'_','')+' depth/length '+str(parameter['Length'])+' mm')
        parameter_text = 'Native feature parameters: '+('; '.join(summary) or 'see constrained source sketches')
        for i in range(4):
            fields['Notes'+str(i+5)] = parameter_text[i*130:(i+1)*130] or ' '
        template.EditableTexts = fields
        record = {'sheet':sheet, 'page':page.Name,'part_number':pn,'source':body.Name,
            'instances':rec['instances'],'material':str(getattr(body,'MaterialName','')),
            'process':process,'scale':scale,'bbox_extents_xyz_mm':list(extent),'dimensions':[],
            'native_feature_parameters':parameters,'critical_fits':'UNKNOWN',
            'views':[], 'errors':[], 'exports':{}}
        views = {}
        specs = [('XY',(0,0,1),(1,0,0),76,127),
                 ('XZ',(0,-1,0),(1,0,0),76,61),
                 ('YZ',(1,0,0),(0,1,0),212,127),
                 ('ISO',(1,-1,1),(1,1,0),212,61)]
        for label,direction,xdir,x,y in specs:
            view = doc.addObject('TechDraw::DrawViewPart', prefix+body.Name+'_'+label)
            view.Label = pn+' '+label;view.Source=[body]
            view.Direction=App.Vector(*direction);view.XDirection=App.Vector(*xdir)
            view.ScaleType='Custom';view.Scale=scale
            view.HardHidden=False;view.SmoothVisible=True
            page.addView(view);view.X=x;view.Y=y
            _view_style(view);views[label]=view;record['views'].append(view.Name)
            _annotation(doc,page,body.Name+'_'+label+'_Label',[label],x,y-24)
        doc.recompute()
        for axis, index, plane, x, y in [('x',0,'XY',76,95),('y',1,'XY',24,127),('z',2,'YZ',260,127)]:
            try:
                _extent(doc,page,body,views[plane],axis,extent[index],x,y,record['dimensions'])
            except Exception as exc:
                record['errors'].append(str(exc))
        # Circular features: one native diameter per distinct radius; all actual
        # projected feature edges retained in manifest, avoiding repeated labels.
        seen = set();circles_by_plane={};record['projected_circular_features']=[]
        for plane in ('XY','XZ','YZ'):
            view=views[plane];circles=_circles(view);circles_by_plane[plane]=circles
            for edge,radius,center in circles:
                record['projected_circular_features'].append({'view':plane,'edge_index':edge,'diameter_mm':radius*2,'center_projected_mm':[center.x,center.y]})
                key=round(radius,7)
                if key in seen:
                    continue
                seen.add(key);slot=len(seen)-1
                # Lower margin has up to 12 clear notes/diameter positions.
                try:
                    _dimension(doc,page,view,body.Name+'_Dia_'+str(slot),'Diameter',
                        ['Edge'+str(edge)],radius*2,28+slot%6*46,40-slot//6*9,
                        record['dimensions'],caption='circular feature')
                except Exception as exc:
                    record['errors'].append(str(exc))
        # A pitch between distinct same-radius circular features. HLR includes
        # genuine center vertices; locate their indexed representations exactly.
        for plane,circles in circles_by_plane.items():
            vertices=_indexed_vertices(views[plane]);pitch_done=False
            for c1,c2 in itertools.combinations(circles,2):
                if abs(c1[1]-c2[1])>TOL or (c1[2]-c2[2]).Length<TOL:
                    continue
                matched=[]
                for circle in (c1,c2):
                    matches=[i for i,p in vertices if (p-circle[2]).Length<TOL]
                    if not matches:break
                    matched.append(matches[0])
                if len(matched)!=2:continue
                try:
                    _dimension(doc,page,views[plane],body.Name+'_Pitch_'+plane,'Distance',
                        ['Vertex'+str(i) for i in matched],float((c1[2]-c2[2]).Length),
                        212,92,record['dimensions'],caption='pivot/feature pitch')
                    pitch_done=True
                except ValueError:
                    continue
                if pitch_done:break
            if pitch_done:break
        doc.recompute()
        manifest['sheets'].append(record)
        manifest['errors'].extend(record['errors'])
    manifest['status']='FAIL' if manifest['errors'] else 'PASS_NATIVE_DIMENSIONS'
    manifest['sheet_count']=len(manifest['sheets'])
    manifest['dimension_count']=sum(len(r['dimensions']) for r in manifest['sheets'])
    manifest['visual_review']='NOT_RUN - lead must inspect rendered PDF pages'
    path=out/('drawing_manifest_'+revision+'.json');path.write_text(json.dumps(manifest,indent=2)+'\n')
    if strict and manifest['errors']:
        raise RuntimeError('Native drawing extent gate failed; see '+str(path)+': '+str(manifest['errors'][:4]))
    # Native construction and GUI layout are separate steps. Never export the
    # initial absolute-coordinate positions used while references are created.
    layout_existing_pages(doc,root,require_gui=export,revision=revision)
    if export:
        export_existing_pages(doc,root,revision=revision)
    return json.loads(path.read_text())


def export_existing_pages(doc, root, sheets=None, revision='r07'):
    """Lead GUI exporter for the saved companion: no view/page construction.

    ``sheets`` optionally selects 1-based sheet numbers for bounded GUI export.
    Reads verified manifest associations, exports only pre-existing native pages,
    and preserves their geometry checks. Does not recompute or save a document.
    """
    import TechDrawGui
    revision=_revision(revision)
    root=Path(root).resolve();out=root/'drawings'/revision
    path=out/('drawing_manifest_'+revision+'.json')
    manifest=json.loads(path.read_text())
    selected=set(sheets) if sheets is not None else None
    targets=[r for r in manifest['sheets'] if selected is None or r['sheet'] in selected]
    for record in targets:
        layout=record.get('layout',{})
        if layout.get('status')!='PASS_NATIVE_REFS_VALUES_UNCHANGED' or not all(
                p.get('style',{}).get('gui_provider') for p in layout.get('placements',[])):
            raise RuntimeError('Apply layout_existing_pages in the GUI before exporting sheet '+str(record['sheet']))
    exported=[]
    for record in manifest['sheets']:
        if selected is not None and record['sheet'] not in selected:
            continue
        page=doc.getObject(record['page'])
        if page is None or page.TypeId != 'TechDraw::DrawPage':
            raise ValueError('Verified native drawing page missing: '+record['page'])
        stem='%03d_%s'%(record['sheet'],_stem(record['part_number']))
        for kind,writer in [('svg',TechDrawGui.exportPageAsSvg),('pdf',TechDrawGui.exportPageAsPdf)]:
            artifact=out/(stem+'.'+kind);writer(page,str(artifact))
            if not artifact.exists() or not artifact.stat().st_size:
                raise IOError('Missing drawing export '+str(artifact))
            record['exports'][kind]=str(artifact)
        record['export_layout_status']='EXPORTED_CURRENT_NATIVE_LAYOUT'
        exported.append(record['sheet'])
    manifest['pdf_exports']='COMPLETE' if all(r['exports'].get('pdf') and r.get('export_layout_status')=='EXPORTED_CURRENT_NATIVE_LAYOUT' for r in manifest['sheets']) else 'PARTIAL'
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    return {'exported_sheets':exported,'sheet_count':len(exported),'manifest':str(path),
            'visual_review':'NOT_RUN - render and inspect final PDFs'}


def _layout_view_extents(record, plane):
    x,y,z=record['bbox_extents_xyz_mm'];scale=record['scale']
    width,height={'XY':(x,y),'XZ':(x,z),'YZ':(y,z),
                  'ISO':((x+y)/math.sqrt(2),(x+y+2*z)/math.sqrt(6))}[plane]
    return width*scale/2,height*scale/2


def _layout_extent_axis(dim):
    match=re.search(r'_(x|y|z)(?:Extent|CircularExtent|_REF_Extent)',dim.Name+' '+dim.Label)
    return match.group(1) if match else None


def _apply_gui_style(obj, dimension=False):
    vo=getattr(obj,'ViewObject',None)
    if vo is None:return {'gui_provider':False}
    desired={'Font':'DejaVu Sans','Fontsize':3.0,
             'LineWidth':.18 if dimension else .25,'HiddenWidth':.13}
    if dimension:desired['Arrowsize']=1.6
    applied={}
    for prop,value in desired.items():
        if prop in vo.PropertiesList:
            setattr(vo,prop,value);applied[prop]=value
    if obj.TypeId=='TechDraw::DrawViewAnnotation':
        obj.TextSize=2.6
        if 'Font' in obj.PropertiesList:obj.Font='DejaVu Sans'
    return {'gui_provider':True,'applied':applied}


def layout_existing_pages(doc, root, sheets=None, require_gui=True, revision='r07'):
    """Fix page layout without changing any native geometry references/values.

    Dimension X/Y are *scaled drawing mm relative to the parent view*, with
    +Y upwards, unlike free annotation positions which are absolute page mm.
    GUI view providers must exist to persist text/arrow/line styles. No document
    save or artifact export occurs. Probe sheets=[1], export/render it, inspect,
    then apply the accepted helper to all sheets before the final GUI save.
    """
    import textwrap
    revision=_revision(revision);prefix=revision.upper()+'Drawing_'
    root=Path(root).resolve();path=root/'drawings'/revision/('drawing_manifest_'+revision+'.json')
    manifest=json.loads(path.read_text());selected=set(sheets) if sheets is not None else None
    targets=[r for r in manifest['sheets'] if selected is None or r['sheet'] in selected]
    if not targets:raise ValueError('No verified drawing sheets selected for layout')
    # Check providers and original measurement evidence before making changes.
    for record in targets:
        for dimrec in record['dimensions']:
            dim=doc.getObject(dimrec['object'])
            if dim is None:raise ValueError('Native dimension missing '+dimrec['object'])
            if require_gui and getattr(dim,'ViewObject',None) is None:
                raise RuntimeError('layout_existing_pages requires the lead GUI document; no dimension view provider')
            if abs(float(dim.getRawValue())-dimrec['expected_mm'])>TOL:
                raise ValueError('Original native dimension no longer matches source '+dim.Name)
            if dim.Arbitrary:raise ValueError('Unexpected arbitrary override '+dim.Name)
    reports=[]
    for record in targets:
        page=doc.getObject(record['page']);views={}
        for name in record['views']:
            view=doc.getObject(name)
            plane=view.Label.rsplit(' ',1)[-1]
            views[plane]=view;_apply_gui_style(view)
        labels={'XY':(22,156),'YZ':(158,156),'XZ':(22,90),'ISO':(158,90)}
        for plane,(x,y) in labels.items():
            label=doc.getObject(prefix+record['source']+'_'+plane+'_Label')
            if label is not None:
                label.X=x;label.Y=y;label.Text=[plane];label.TextSize=2.6
                _apply_gui_style(label)
        fields=dict(page.Template.EditableTexts)
        # Break at words/feature separators rather than slicing a decimal value.
        summary=[]
        for parameter in record.get('native_feature_parameters',[]):
            if 'Length' in parameter:
                summary.append(parameter['object'].replace(record['source']+'_','')+
                               ' depth/length '+format(parameter['Length'],'.4g')+' mm')
        text='Native feature parameters: '+('; '.join(summary) or 'see constrained source sketches')
        lines=textwrap.wrap(text,width=125,break_long_words=False,break_on_hyphens=False)
        for i in range(4):fields['Notes'+str(i+5)]=lines[i] if i<len(lines) else ' '
        fields['Note']='Dimensions mm. DESIGN_ASSUMPTION. Critical fits UNKNOWN. Validate interfaces and loads. Do not scale.'
        page.Template.EditableTexts=fields
        dimensions=[];diameters={plane:[] for plane in views}
        for dimrec in record['dimensions']:
            dim=doc.getObject(dimrec['object']);before=float(dim.getRawValue())
            refs_before=repr(dim.References2D),repr(dim.References3D)
            parent=dim.References2D[0][0] if dim.References2D else None
            if parent is None:
                axis=_layout_extent_axis(dim);parent=views['YZ' if axis=='z' else 'XY']
            plane=parent.Label.rsplit(' ',1)[-1];hx,hy=_layout_view_extents(record,plane)
            style=_apply_gui_style(dim,True)
            dim.ShowUnits=False;dim.FormatSpec='%.2f'
            axis=_layout_extent_axis(dim)
            if axis:
                if dim.Type=='Diameter':
                    # Two envelope diameter references remain native/editable;
                    # spread them left above/below with explicit X/Y REF labels.
                    dim.X=-(hx+12);dim.Y=(hy+8)*(1 if axis=='y' else -1)
                    dim.FormatSpec='\u00d8%.2f '+axis.upper()+' REF'
                elif dim.Type=='DistanceX':dim.X=0.;dim.Y=-(hy+9)
                elif dim.Type in ('DistanceY','DistanceZ'):
                    dim.X=-(hx+9);dim.Y=0.
                    # Keep labels of sub-4mm projected thickness dimensions
                    # above their very short line rather than over arrowheads.
                    if dimrec['expected_mm']*record['scale']<4:dim.Y=hy+6
                else:dim.X=0.;dim.Y=-(hy+9)
            elif dim.Type=='Diameter':
                dim.FormatSpec='\u00d8%.2f'
                center=None
                for obj,names in dim.References2D:
                    for name in names:
                        if name.startswith('Edge'):
                            curve=obj.getEdgeByIndex(int(name[4:])).Curve
                            if hasattr(curve,'Center'):
                                center=(float(curve.Center.x)*record['scale'],float(curve.Center.y)*record['scale'])
                diameters[plane].append((dim,center or (0.,0.)))
            else:
                points=[]
                for obj,names in dim.References2D:
                    for name in names:
                        if name.startswith('Vertex'):
                            p=obj.getVertexByIndex(int(name[6:])).Point
                            points.append((p.x*record['scale'],p.y*record['scale']))
                if len(points)>=2:
                    dx=points[1][0]-points[0][0];dy=points[1][1]-points[0][1]
                    mx=(points[1][0]+points[0][0])/2;my=(points[1][1]+points[0][1])/2
                    if abs(dx)<abs(dy)*.25:dim.X=-(hx+20);dim.Y=my
                    elif abs(dy)<abs(dx)*.25:dim.X=mx;dim.Y=hy+9
                    else:
                        length=math.hypot(dx,dy);offset=max(hx,hy)/2+9
                        dim.X=max(-54.,min(54.,mx-dy/length*offset))
                        dim.Y=max(-32.,min(32.,my+dx/length*offset))
                else:dim.X=0.;dim.Y=hy+9
            vo=getattr(dim,'ViewObject',None)
            if vo is not None and 'FlipArrowheads' in vo.PropertiesList:
                vo.FlipArrowheads=(dim.Type!='Diameter' and dimrec['expected_mm']*record['scale']<4)
            dimensions.append({'object':dim.Name,'parent':parent.Name,'plane':plane,
                'before_mm':before,'refs_before':refs_before,'style':style,'dimension':dim})
        # Match leader order to feature-center height. Same-height feature on
        # the right gets the lower/central slot, reducing crossovers through
        # another bore. All leader labels stay next to their own parent view.
        for plane,items in diameters.items():
            hx,hy=_layout_view_extents(record,plane);n=len(items)
            items.sort(key=lambda item:(-item[1][1],item[1][0]))
            gap=8.;span=(n-1)*gap
            if span>max(2*hy+12,24):gap=max(2*hy+12,24)/max(n-1,1)
            for i,(dim,center) in enumerate(items):
                dim.X=hx+15
                dim.Y=((n-1)/2-i)*gap
        doc.recompute()
        placements=[]
        expected_by_name={r['object']:r['expected_mm'] for r in record['dimensions']}
        for item in dimensions:
            dim=item.pop('dimension');expected=expected_by_name[dim.Name]
            after=float(dim.getRawValue())
            if abs(after-expected)>TOL or item.pop('refs_before')!=(repr(dim.References2D),repr(dim.References3D)):
                raise ValueError('Layout changed native geometry reference/value '+dim.Name)
            parent=doc.getObject(item['parent'])
            placements.append({**item,'local_x_mm':float(dim.X),'local_y_mm':float(dim.Y),
                'page_label_center_x_mm':float(parent.X+dim.X),
                'page_label_center_y_mm':float(parent.Y+dim.Y),
                'raw_value_mm':after,'absolute_error_mm':abs(after-expected)})
        report={'sheet':record['sheet'],'status':'PASS_NATIVE_REFS_VALUES_UNCHANGED',
            'coordinate_system':'dimension X/Y are scaled mm relative to parent view; +Y up',
            'dimension_font_mm':3.,'arrow_size_mm':1.6,'dimension_line_width_mm':.18,
            'view_line_width_mm':.25,'units':'mm (global template note)',
            'placements':placements,'visual_review':'NOT_RUN - export and inspect this layout'}
        record['layout']=report;record['export_layout_status']='STALE_AFTER_LAYOUT_CHANGE'
        reports.append(report)
    manifest['pdf_exports']='PARTIAL_OR_STALE - layout changes need fresh GUI export'
    manifest['visual_review']='NOT_RUN - layout correction requires rendered PDF inspection'
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    return {'sheets':reports,'sheet_count':len(reports),'saved_document':False,'exported_artifacts':False}
