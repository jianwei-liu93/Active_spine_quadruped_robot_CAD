"""Lead-GUI layout adapter for the frozen 77-sheet r10 staged companion.

Preparation/import has no side effects. run() adjusts drawing presentation and
its manifest only; never constructs geometry, saves CAD or exports artifacts.
"""
from pathlib import Path
import hashlib
import json
import math

NATIVE_SHA256 = 'd90c7dba99b8a5f0825160d4c1d2058509ce64401e95b49aa4101fc66b8e9ad9'
STAGING_SHA256 = '26fb62d0727f73fccb6e814e50f32dd1f4a3669e2958bb8c54c9f137d9c93164'
TOL = 1e-6
INTERFACES = ('ClevisBore_fore', 'ClevisBore_hind', 'LugThroughBoreE1',
              'LugBearingSeatE1', 'LugThroughBoreE2', 'LugBearingSeatE2',
              'PinOD', 'PinGrooveRoot', 'RetainerID', 'RetainerOD')


def _require(value, message):
    if not value:
        raise ValueError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _number(value):
    value = float(value)
    _require(math.isfinite(value), 'Nonfinite drawing value')
    return value


def _refs(values):
    return [(obj.Name, tuple(names)) for obj, names in values]


def _measurement(dim):
    return {'refs2d': _refs(dim.References2D), 'refs3d': _refs(dim.References3D),
            'raw_mm': _number(dim.getRawValue()), 'arbitrary': bool(dim.Arbitrary)}


def _object(doc, name, kind=None):
    obj = doc.getObject(name)
    _require(obj is not None and (kind is None or obj.TypeId == kind),
             'Missing/wrong native drawing object: ' + name)
    return obj


def _same_measurement(dim, before, expected):
    after = _measurement(dim)
    _require(not after['arbitrary'] and after['arbitrary'] == before['arbitrary'] and
             after['refs2d'] == before['refs2d'] and after['refs3d'] == before['refs3d'] and
             abs(after['raw_mm'] - before['raw_mm']) <= TOL and
             abs(after['raw_mm'] - expected) <= TOL,
             'Layout changed native references/value/Arbitrary: ' + dim.Name)
    return after


def _auxiliary(doc, record):
    """Read-only preflight of one actual projected/source circular-arc pair."""
    _require(len(record['views']) == len(record['dimensions']) == 1,
             'Auxiliary sheet must have one native view and diameter')
    row = record['dimensions'][0]
    _require(row['type'] == 'Diameter' and row['reference_space'] == '2D_NATIVE' and
             row.get('arbitrary') is False and row['source_object'] == record['source'],
             'Auxiliary diameter provenance differs from staged evidence')
    view = _object(doc, record['views'][0], 'TechDraw::DrawViewPart')
    page = _object(doc, record['page'], 'TechDraw::DrawPage')
    dim = _object(doc, row['object'], 'TechDraw::DrawViewDimension')
    source = _object(doc, record['source'], 'PartDesign::Body')
    _require(dim.Type == 'Diameter' and dim.MeasureType == 'Projected' and
             [o.Name for o in view.Source] == [source.Name], 'Auxiliary source/view ownership changed')
    _require(view in page.Views and dim in page.Views, 'Auxiliary view/dimension not owned by expected page')
    before = _measurement(dim)
    expected = _number(row['expected_mm'])
    _require(expected > 0 and not before['arbitrary'] and
             abs(before['raw_mm'] - expected) <= TOL and not before['refs3d'] and
             before['refs2d'] == [(view.Name, tuple(row['references']))],
             'Auxiliary native reference/raw diameter mismatch')
    edge_index = row['projected_edge_index']
    _require(type(edge_index) is int and edge_index >= 0 and row['references'] == ['Edge' + str(edge_index)],
             'Auxiliary projected edge identity mismatch')
    curve = view.getEdgeByIndex(edge_index).Curve
    _require(hasattr(curve, 'Radius') and abs(2 * curve.Radius - expected) <= TOL,
             'Auxiliary actual projected circular arc diameter changed')
    _require(all(abs(_number(curve.Center[i]) - row['projected_center_mm'][i]) <= TOL for i in range(3)),
             'Auxiliary projected circular-arc center changed')
    source_edge = row['source_edge']
    native_index = source_edge['edge_index_1based']
    _require(type(native_index) is int and 1 <= native_index <= len(source.Shape.Edges) and
             source_edge['edge'] == 'Edge' + str(native_index), 'Auxiliary source arc identity invalid')
    native_curve = source.Shape.Edges[native_index - 1].Curve
    _require(hasattr(native_curve, 'Radius') and abs(2 * native_curve.Radius - expected) <= TOL and
             abs(_number(source_edge['diameter_mm']) - expected) <= TOL and
             all(abs(_number(native_curve.Center[i]) - source_edge['center_source_local_xyz_mm'][i]) <= TOL
                 for i in range(3)), 'Auxiliary original source circular-arc diameter/center changed')
    # All ten staged projections are normal to source Z with source X right.
    _require(all(abs(_number(view.Direction[i]) - source_edge['axis_source_local_xyz'][i]) <= TOL
                 for i in range(3)) and
             all(abs(_number(view.XDirection[i]) - (1., 0., 0.)[i]) <= TOL for i in range(3)) and
             abs(abs(_number(view.Direction[2])) - 1.) <= TOL,
             'Auxiliary source-Z projection convention changed')
    scale = _number(record['scale'])
    _require(scale > 0 and abs(_number(view.Scale) - scale) <= TOL, 'Auxiliary view scale changed')
    hx = _number(record['bbox_extents_xyz_mm'][0]) * scale / 2
    hy = _number(record['bbox_extents_xyz_mm'][1]) * scale / 2
    _require(hx > 0 and hy > 0, 'Auxiliary view extent invalid')
    x, y = hx + 15., hy + 8.
    px, py = _number(view.X) + x, _number(view.Y) + y
    _require(20. <= px <= 277. and 35. <= py <= 190.,
             'Auxiliary diameter label would fall outside usable A4 landscape page')
    return dim, view, before, expected, x, y


def run(doc, root, sheets=None, expected_native_sha256=NATIVE_SHA256,
        expected_staging_sha256=STAGING_SHA256):
    """Lead runs on the opened staged GUI companion; saves/exports separately.

    sheets=None selects all77; subsets allow bounded GUI visual probes.
    All selected objects are preflighted before any presentation mutation.
    """
    import drawings_r07 as drawing
    root = Path(root).resolve()
    manifest_path = root / 'drawings/r10/drawing_manifest_r10.json'
    manifest = json.loads(manifest_path.read_text())
    native = (root / 'cad/flexor_r10_robot.FCStd').resolve()
    staged = (root / 'cad/staging/r10_drawings_prepared.FCStd').resolve()
    _require(_sha(native) == manifest.get('source_sha256') == expected_native_sha256,
             'Canonical/manifest source SHA changed')
    _require(_sha(staged) == manifest.get('staging_native_sha256') == expected_staging_sha256 and
             Path(doc.FileName).resolve() == staged, 'Open the expected frozen staged drawing document')
    rows = manifest['sheets']
    _require(manifest.get('revision') == 'r10' and manifest.get('status') == 'PASS_NATIVE_DIMENSIONS' and
             not manifest.get('errors') and manifest.get('sheet_count') == len(rows) == 77 and
             [r['sheet'] for r in rows] == list(range(1, 78)) and
             [r.get('interface_key') for r in rows[67:]] == list(INTERFACES) and
             not any(r.get('interface_key') for r in rows[:67]) and
             manifest.get('dimension_count') == sum(len(r['dimensions']) for r in rows),
             'Expected exact77-sheet native manifest with ten interface sheets')
    selected = set(range(1, 78)) if sheets is None else set(sheets)
    _require(selected and all(type(n) is int and 1 <= n <= 77 for n in selected), 'Invalid drawing sheet selection')
    targets = [r for r in rows if r['sheet'] in selected]
    original = {}
    auxiliary = {}
    for record in targets:
        _require(not record.get('errors'), 'Selected drawing sheet has errors')
        page = _object(doc, record['page'], 'TechDraw::DrawPage')
        for name in record['views']:
            view = _object(doc, name, 'TechDraw::DrawViewPart')
            _require(view in page.Views and getattr(view, 'ViewObject', None) is not None,
                     'Lead GUI view provider is required before layout')
        for row in record['dimensions']:
            dim = _object(doc, row['object'], 'TechDraw::DrawViewDimension')
            _require(getattr(dim, 'ViewObject', None) is not None, 'Lead GUI dimension provider required')
            before = _measurement(dim)
            _require(not before['arbitrary'] and abs(before['raw_mm'] - row['expected_mm']) <= TOL,
                     'Original native measurement no longer matches staged evidence')
            _require(dim.Name not in original, 'Duplicate native dimension in selected sheets')
            original[dim.Name] = before
        if record['sheet'] >= 68:
            auxiliary[record['sheet']] = _auxiliary(doc, record)
    regular = sorted(selected & set(range(1, 68)))
    reports = []
    if regular:
        reports.extend(drawing.layout_existing_pages(doc, root, sheets=regular,
                       require_gui=True, revision='r10')['sheets'])
    # The reused helper updates the manifest; retain its regular-sheet reports.
    manifest = json.loads(manifest_path.read_text())
    for record in manifest['sheets']:
        if record['sheet'] not in auxiliary:
            continue
        dim, view, before, expected, x, y = auxiliary[record['sheet']]
        view_style = drawing._apply_gui_style(view)
        style = drawing._apply_gui_style(dim, dimension=True)
        _require(view_style.get('gui_provider') is True and style.get('gui_provider') is True,
                 'GUI styling provider disappeared')
        dim.ShowUnits = False
        dim.FormatSpec = '\u00d8%.2f'
        dim.X, dim.Y = x, y
        doc.recompute()
        after = _same_measurement(dim, before, expected)
        report = {'sheet': record['sheet'], 'status': 'PASS_NATIVE_REFS_VALUES_UNCHANGED',
            'coordinate_system': 'dimension X/Y are scaled mm relative to parent view; +Y up',
            'dimension_font_mm': 3., 'arrow_size_mm': 1.6, 'dimension_line_width_mm': .18,
            'view_line_width_mm': .25, 'units': 'mm (global template note)',
            'interface_key': record['interface_key'], 'view_style': view_style,
            'placements': [{'object': dim.Name, 'parent': view.Name, 'plane': 'SOURCE_Z_NORMAL',
                'before_mm': before['raw_mm'], 'style': style,
                'local_x_mm': _number(dim.X), 'local_y_mm': _number(dim.Y),
                'page_label_center_x_mm': _number(view.X) + _number(dim.X),
                'page_label_center_y_mm': _number(view.Y) + _number(dim.Y),
                'raw_value_mm': after['raw_mm'], 'absolute_error_mm': abs(after['raw_mm'] - expected),
                'references_2d': after['refs2d'], 'references_3d': after['refs3d'], 'arbitrary': False,
                'source_edge': record['dimensions'][0]['source_edge']}],
            'visual_review': 'NOT_RUN - export and inspect this layout'}
        record['layout'] = report
        record['export_layout_status'] = 'STALE_AFTER_LAYOUT_CHANGE'
        reports.append(report)
    for record in targets:
        for row in record['dimensions']:
            _same_measurement(doc.getObject(row['object']), original[row['object']], row['expected_mm'])
    _require(_sha(native) == expected_native_sha256 and _sha(staged) == expected_staging_sha256,
             'Frozen native files changed during layout')
    manifest['pdf_exports'] = 'PARTIAL_OR_STALE - layout changes need fresh GUI export'
    manifest['visual_review'] = 'NOT_RUN - layout correction requires rendered PDF inspection'
    manifest['gui_styles'] = 'APPLIED_TO_SELECTED_SHEETS - save/export and visual review remain lead gates'
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    return {'sheets': sorted(reports, key=lambda r: r['sheet']), 'sheet_count': len(reports),
            'saved_document': False, 'exported_artifacts': False,
            'source_geometry_changed': False, 'visual_review': 'NOT_RUN'}
