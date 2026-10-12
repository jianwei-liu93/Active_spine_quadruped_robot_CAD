"""Build the r10 assembly and calibration PDF from final revision-matched evidence.

The generator deliberately refuses to publish a PDF until the frozen r10
package, native, composite motion, AX0/AX1, drawing, profile, mass and engineering-screen records
are present and pass their declared gates. It writes only the owned r10 PDF
and cropped copies of actual r10 FreeCAD captures.
"""
from __future__ import print_function

import csv
import hashlib
import json
import importlib.util
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
    Spacer, Table, TableStyle, Image, PageBreak, LongTable, KeepTogether)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/flexor_r10_assembly_calibration.pdf'
VIEW_DIR = ROOT / 'reports/views/manual_r10'
PAGE_W, PAGE_H = A4
NAVY = colors.HexColor('#173247')
TEAL = colors.HexColor('#18838B')
ORANGE = colors.HexColor('#D16C43')
PALE = colors.HexColor('#EDF4F5')
PALE_ORANGE = colors.HexColor('#FFF1E9')
INK = colors.HexColor('#243642')
MID = colors.HexColor('#5A6B75')
GRID = colors.HexColor('#D1DDE1')
PACKAGE_STATUS = 'EXPORTS_AND_STEP_ROUNDTRIP_VALIDATED_NO_FABRICATION_RELEASE'
CAPTURE_NAMES = ('r10_robot_assembled.png', 'r10_robot_side.png',
                 'r10_spine_source_facing.png', 'r10_bare_lumbar_pos_y_oblique.png',
                 'r10_bare_lumbar_neg_y_oblique.png', 'r10_central_attachment_bare.png',
                 'r10_fore_plate_profile.png', 'r10_hind_plate_profile.png', 'r10_long_bar_profile.png')


def safe(text):
    text = str(text)
    for a, b in (('\u2013', '-'), ('\u2014', '-'), ('\u2212', '-'),
                 ('\u00d7', 'x'), ('\u00d8', 'dia.'), ('\u00b0', ' deg'),
                 ('\u00b7', ' '), ('\u2264', '<='), ('\u2265', '>=')):
        text = text.replace(a, b)
    return text


def styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('r10title', parent=base['Title'], fontName='Helvetica-Bold',
            fontSize=27, leading=31, textColor=NAVY, spaceAfter=8),
        'subtitle': ParagraphStyle('r10subtitle', parent=base['Normal'], fontSize=12,
            leading=17, textColor=MID, spaceAfter=10),
        'h1': ParagraphStyle('r10h1', parent=base['Heading1'], fontName='Helvetica-Bold',
            fontSize=18, leading=22, textColor=NAVY, spaceAfter=8, keepWithNext=True),
        'h2': ParagraphStyle('r10h2', parent=base['Heading2'], fontName='Helvetica-Bold',
            fontSize=11.5, leading=14, textColor=TEAL, spaceBefore=8, spaceAfter=4, keepWithNext=True),
        'body': ParagraphStyle('r10body', parent=base['BodyText'], fontName='Helvetica',
            fontSize=8.7, leading=12, textColor=INK, spaceAfter=6),
        'small': ParagraphStyle('r10small', parent=base['BodyText'], fontName='Helvetica',
            fontSize=7.4, leading=9.5, textColor=INK, spaceAfter=3),
        'caption': ParagraphStyle('r10caption', parent=base['BodyText'], fontName='Helvetica-Oblique',
            fontSize=7.4, leading=9, textColor=MID, alignment=1, spaceBefore=3, spaceAfter=6),
        'th': ParagraphStyle('r10th', parent=base['BodyText'], fontName='Helvetica-Bold',
            fontSize=7.2, leading=9, textColor=colors.white, spaceAfter=0),
        'td': ParagraphStyle('r10td', parent=base['BodyText'], fontName='Helvetica',
            fontSize=7.2, leading=9, textColor=INK, spaceAfter=0),
        'center': ParagraphStyle('r10center', parent=base['BodyText'], fontName='Helvetica-Bold',
            fontSize=8, leading=10, textColor=NAVY, alignment=1),
    }


def p(text, style):
    return Paragraph(safe(text), style)


def read_json(rel, required=False):
    path = ROOT / rel
    if not path.exists():
        if required:
            raise RuntimeError('Required final r10 evidence is missing: ' + rel)
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _module(name):
    """Load a read-only Python evidence helper without depending on sys.path."""
    spec = importlib.util.spec_from_file_location(name, ROOT / 'src' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _native_hash(record):
    return (record.get('native_sha256') or record.get('canonical_robot_sha256')
            or record.get('source_sha256') or record.get('final_canonical_sha256'))


def gate_evidence(expected_native_sha256):
    """Read-only acceptance. The lead must explicitly supply the frozen SHA.

    Importing this module never opens CAD, creates a PDF or writes any report.
    The changed-pair aggregation is rechecked against its pinned
    partitions; a historical r08 PASS alone cannot satisfy the r10 motion gate.
    """
    _require(isinstance(expected_native_sha256, str) and len(expected_native_sha256) == 64
             and all(c in '0123456789abcdef' for c in expected_native_sha256),
             'Supply the lead-frozen r10 native SHA256 explicitly')
    required = {
        'package': 'reports/package_manifest_r10.json',
        'native_check': 'reports/verification/r10_native_checks.json',
        'reproduction': 'reports/verification/r10_source_reproduction.json',
        'mass': 'reports/verification/r10_mass_envelope.json',
        'engineering': 'reports/verification/r10_engineering_screen.json',
        'neutral': 'reports/verification/r10_neutral.json',
        'motion': 'reports/verification/r10_changed_partitions/summary.json',
        'drawings': 'drawings/r10/drawing_manifest_r10.json',
        'profiles': 'exports/profiles/r10/profile_manifest_r10.json',
        'capture': 'reports/views/r10_capture_manifest.json',
        'ax01': 'reports/animation/ax01_r10.json',
        'poses': 'animation/motion/ax01_r10.json',
    }
    data = {key: read_json(path, required=True) for key, path in required.items()}
    native = ROOT / 'cad/flexor_r10_robot.FCStd'
    native_sha = sha256(native)
    _require(native_sha == expected_native_sha256, 'Native differs from lead-frozen r10 SHA')
    package = data['package']
    _require(package.get('revision') == 'r10' and package.get('status') == PACKAGE_STATUS,
             'r10 package manifest is not in the validated export state')
    _require((package.get('native_document') or {}).get('sha256') == native_sha,
             'Package native SHA does not match final r10 native')
    for key in ('mass', 'neutral', 'drawings', 'profiles', 'capture'):
        _require(data[key].get('revision') == 'r10', key + ' record is not revision r10')
    for key in ('mass', 'engineering', 'neutral', 'drawings', 'profiles', 'capture'):
        _require(_native_hash(data[key]) == native_sha,
                 key + ' must identify the final canonical r10 SHA (staging evidence is insufficient)')
    _require(data['neutral'].get('status') == 'PASS', 'r10 primary neutral check is not PASS')
    _require(data['drawings'].get('visual_review') == 'PASS'
             and data['drawings'].get('pdf_exports') in ('PASS', 'COMPLETE'),
             'r10 drawing PDF export and visual review must both pass')
    sheets = data['drawings'].get('sheets', [])
    _require(sheets and len(sheets) == data['drawings'].get('sheet_count')
             and sum(len(s.get('dimensions', [])) for s in sheets) == data['drawings'].get('dimension_count'),
             'Drawing counts disagree with actual sheet/dimension records')
    _require(not data['drawings'].get('errors'), 'Drawing manifest has errors')
    _require(data['profiles'].get('status') in ('PASS', 'PASS_EXACT_PROFILE_READBACK'),
             'r10 profile round-trip check is not PASS')
    _require(data['capture'].get('visual_review') == 'PASS', 'r10 source-fidelity image review is not PASS')
    captures = {r['path']: r for r in data['capture'].get('captures', [])}
    for name in CAPTURE_NAMES:
        rel = 'reports/views/' + name
        _require(rel in captures and sha256(ROOT / rel) == captures[rel].get('sha256'),
                 'Missing/stale canonical r10 capture: ' + rel)
    _require(data['mass'].get('status') == 'COMPUTED_FROM_DOCUMENT', 'r10 mass calculation is incomplete')
    _require(data['engineering'].get('native_document') == str(native),
             'Engineering screen does not identify final r10 document')
    count = data['mass'].get('instance_count')
    _require(count == 487 and package.get('physical_link_count') == count
             and data['neutral'].get('instances') == count
             and data['engineering'].get('physical_link_count') == count,
             'r10 physical inventory disagrees across final records')
    _require(package.get('bom_mass_summary', {}).get('part_number_count') == data['mass'].get('part_number_count'),
             'Package and mass report part-number counts disagree')
    _require(math.isclose(data['engineering']['known_mass']['mass_g'],
                         data['mass']['known_mass_sum_g'], rel_tol=1e-10, abs_tol=1e-8),
             'Engineering screen and mass report known mass disagree')
    _gate_native_and_exports(data, native_sha)
    _gate_motion(data['motion'], native_sha)
    _gate_animation(data['ax01'], data['poses'], native_sha, count)
    return data, native_sha


def _gate_native_and_exports(data, native_sha):
    adapter = _module('package_delivery_r10')
    adapter.FROZEN_NATIVE_SHA256 = native_sha
    with adapter.zipfile.ZipFile(ROOT / 'cad/flexor_r10_robot.FCStd') as archive:
        xml = adapter.ET.fromstring(archive.read('Document.xml'))
    names = {o.get('name') for o in xml.findall('.//Object') if o.get('type') == 'App::Link'}
    bodies = sum(o.get('type') == 'PartDesign::Body' for o in xml.findall('.//Object'))
    adapter.validate_native_state_report(data['native_check'], names, bodies)
    package = data['package']
    adapter.check_geometry(package['assembly_geometry_check'], 487, 'Manual assembly STEP')
    _require(package.get('native_file_unchanged') is True and
             package['clean_document_roundtrip'].get('closed_without_save') is True and
             package['clean_document_roundtrip'].get('solid_count') == 487 and
             package.get('unique_used_definition_count') == len(package['parts']) == 107,
             'Manual strict STEP reimport/source inventory incomplete')
    for part in package['parts']:
        adapter.check_geometry(part['step_geometry_check'], 1, 'Manual unique STEP')
    reproduction = data['reproduction']
    adapter.native_match(reproduction, 'Manual source reproduction')
    _require(reproduction.get('status') == 'PASS' and reproduction.get('native_file_unchanged') is True and
             reproduction.get('instances') == 487 and reproduction.get('source_partdesign_bodies') == 95 and
             reproduction.get('part_numbers_match') is True, 'Source build reproduction gate incomplete')
    adapter.check_geometry(reproduction['comparison'], 487, 'Manual source reproduction')
    _require({r['native_label'] for r in reproduction['comparison']['one_to_one_placed_solids']} == names,
             'Source reproduction instance ledger incomplete')


def _gate_motion(summary, native_sha):
    """Use the same strict read-only changed-pair gate as final delivery."""
    import sys
    source_path = str(ROOT / 'src')
    inserted = source_path not in sys.path
    if inserted:
        sys.path.insert(0, source_path)
    try:
        adapter = _module('package_delivery_r10')
        adapter.FROZEN_NATIVE_SHA256 = native_sha
        with adapter.zipfile.ZipFile(ROOT / 'cad/flexor_r10_robot.FCStd') as archive:
            xml = adapter.ET.fromstring(archive.read('Document.xml'))
        names = {o.get('name') for o in xml.findall('.//Object') if o.get('type') == 'App::Link'}
        adapter.validate_inherited_motion(adapter.read, adapter.path_with_digest, native_sha, names)
    finally:
        if inserted:
            sys.path.remove(source_path)


def _gate_animation(report, payload, native_sha, count):
    _require(report.get('AX0') == report.get('AX1') == 'PASS' and report.get('cad_revision') == 'r10'
             and report.get('native_sha256') == native_sha
             and report.get('document_unchanged') is True and report.get('native_file_unchanged') is True,
             'r10 AX0/AX1 report is incomplete or stale')
    _require(report.get('output') == 'animation/motion/ax01_r10.json'
             and report.get('output_sha256') == sha256(ROOT / 'animation/motion/ax01_r10.json'),
             'AX0/AX1 pose payload hash mismatch')
    _require(payload.get('source', {}).get('cad_sha256') == native_sha
             and payload.get('source', {}).get('cad_revision') == 'r10'
             and report.get('physical_instances') == report.get('effective_motion_coverage') == count
             and len(payload.get('instances', [])) == count, 'AX0/AX1 inventory/native mismatch')
    _module('animation_manifest_validate').validate_manifest(payload)
    from collections import Counter
    _require(report.get('source_definitions') == 107, 'AX used sources must be 107')
    for frame in payload['frames']:
        _require(Counter(r['generator'] for r in frame['procedural_shapes']) == {'spring': 8, 'cable': 2},
                 'AX needs eight deforming springs and two cables at every pose')
    coupling = report.get('command_coupling', {})
    _require(coupling.get('physical_motors') == 7 and coupling.get('commanded_coordinates') == 6
             and coupling.get('prescribed_knees') == 4 and coupling.get('loaded_passive_motion') == 'NOT_SOLVED',
             'AX0/AX1 commanded/prescribed coordinate contract mismatch')
    _require(report.get('source_definitions') == len(payload.get('meshes', [])),
             'AX0/AX1 source-definition count mismatch')
    _require(report.get('grounding_sha256') == sha256(ROOT / 'animation/schema/grounded_instances_r10.json'),
             'AX0/AX1 reviewed grounding supplement changed')
    _require(report.get('exporter_source_sha256') == sha256(ROOT / 'src/animation_pose_export.py'),
             'AX0/AX1 exporter source changed')
    for rel, digest in payload['source'].get('parameter_files_sha256', {}).items():
        _require(sha256(ROOT / rel) == digest, 'AX0/AX1 parameter changed: ' + rel)
    for name, digest in report.get('generator_source_sha256', {}).items():
        _require(sha256(ROOT / 'src' / name) == digest, 'AX0/AX1 generator changed: ' + name)


def bom_rows():
    path = ROOT / 'bom/bom_r10.csv'
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise RuntimeError('bom/bom_r10.csv has no part rows')
    return sorted(rows, key=lambda r: (r.get('part_number', ''),))


def category(pn):
    if pn.startswith('DYNAMIXEL_'):
        return 'Actuators'
    if pn.startswith(('SPN_', 'SPINE_', 'DIRECT_CRANK_', 'G_CRANK_', 'GUIDE_COPPER', 'HORN_')):
        return 'Spine drive and joints'
    if pn.startswith(('FRM_', 'TORSO_', 'FIXED_TIE_', 'MOTOR_CENTER_')):
        return 'Frames and ties'
    if pn.startswith(('OpenRB150_', 'OPENRB150_')):
        return 'Controller and carrier'
    if pn.startswith(('LEG_', 'KNEE_', 'TENDON_')):
        return 'Legs, springs and tendon drive'
    return 'Bearings, clips, spacers and other hardware'


def crop_image(name):
    from PIL import Image as PILImage
    source = ROOT / 'reports/views' / name
    if not source.exists():
        raise RuntimeError('Required r10 FreeCAD capture is missing: ' + str(source))
    VIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = VIEW_DIR / (source.stem + '_crop.png')
    im = PILImage.open(source).convert('RGB')
    w, h = im.size
    im.crop((int(w * .08), int(h * .08), int(w * .91), int(h * .92))).save(target, optimize=True)
    return target


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GRID); canvas.setLineWidth(.5)
    canvas.line(19 * mm, PAGE_H - 13 * mm, PAGE_W - 19 * mm, PAGE_H - 13 * mm)
    canvas.setFillColor(NAVY); canvas.setFont('Helvetica-Bold', 7.5)
    canvas.drawString(19 * mm, PAGE_H - 10.5 * mm, 'FLEXOR-F INSPIRED QUADRUPED | R09')
    canvas.setFillColor(ORANGE)
    canvas.drawRightString(PAGE_W - 19 * mm, PAGE_H - 10.5 * mm, 'REVIEW CANDIDATE - NOT FOR FABRICATION')
    canvas.line(19 * mm, 14 * mm, PAGE_W - 19 * mm, 14 * mm)
    canvas.setFillColor(MID); canvas.setFont('Helvetica', 7)
    canvas.drawString(19 * mm, 9.5 * mm, 'Assembly and torque-off calibration record | 2026-10-12')
    canvas.drawRightString(PAGE_W - 19 * mm, 9.5 * mm, 'Page %d' % doc.page)
    canvas.restoreState()


def make_table(data, widths, repeat=1, header=True):
    table = Table(data, colWidths=widths, repeatRows=repeat if header else 0, hAlign='LEFT')
    commands = [('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('GRID', (0, 0), (-1, -1), .35, GRID)]
    if header:
        commands.extend([('BACKGROUND', (0, 0), (-1, 0), NAVY),
                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.white)])
    table.setStyle(TableStyle(commands))
    return table


def build(expected_native_sha256):
    evidence, native_sha = gate_evidence(expected_native_sha256)
    rows = bom_rows()
    mass = evidence['mass']
    screen = evidence['engineering']
    summary = evidence['package']['bom_mass_summary']
    if len(rows) != mass['part_number_count']:
        raise RuntimeError('r10 BOM row count disagrees with final mass report')
    count = sum(int(r['quantity']) for r in rows)
    quantities = {r['part_number']: int(r['quantity']) for r in rows}
    _require(quantities.get('DYNAMIXEL_XL330_M077_T') == 2
             and quantities.get('DYNAMIXEL_XC330_M181_T') == 5, 'Final BOM motor inventory is not 2 XL + 5 XC')
    _require(quantities.get('FRM_LUMBAR_MONOLITHIC_CAGE_r10') == 1,
             'Final BOM must contain exactly one monolithic lumbar cage')
    if count != mass['instance_count']:
        raise RuntimeError('r10 BOM quantities disagree with final mass report')
    ss = styles()
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=19*mm, rightMargin=19*mm,
        topMargin=19*mm, bottomMargin=19*mm, title='FLEXOR r10 Assembly and Calibration Record',
        author='Engineering review package', subject='Editable review candidate; no fabrication release')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
        leftPadding=0, rightPadding=0, topPadding=1*mm, bottomPadding=1*mm, id='main')
    doc.addPageTemplates([PageTemplate(id='all', frames=[frame], onPage=header_footer)])
    story = []

    # Candidate cover and actual captured assembly views.
    hero = crop_image('r10_robot_assembled.png')
    story += [Spacer(1, 7*mm), p('Assembly &amp; calibration<br/>record', ss['title']),
        p('Review candidate r10 | FLEXOR-F inspired active-spine quadruped', ss['subtitle'])]
    status = Table([[p('EDITABLE CANDIDATE', ss['center']), p('PROVISIONAL INTERFACES', ss['center']),
                     p('NOT FOR FABRICATION', ss['center'])]], colWidths=[doc.width/3]*3)
    status.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE_ORANGE),('BOX',(0,0),(-1,-1),.7,ORANGE),
        ('INNERGRID',(0,0),(-1,-1),.4,colors.white),('TOPPADDING',(0,0),(-1,-1),7),
        ('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story += [status, Spacer(1, 4*mm), Image(str(hero), width=doc.width, height=doc.width*.55),
        p('Actual saved FreeCAD view of the r10 candidate. Motor and controller representations are envelopes; this is not a photograph or supplier-interface verification.', ss['caption'])]
    facts = [[p('<b>{}</b><br/>physical links'.format(count), ss['center']),
              p('<b>{}</b><br/>unique part numbers'.format(len(rows)), ss['center']),
              p('<b>{:.3f} g</b><br/>known mass'.format(mass['known_mass_sum_g']), ss['center']),
              p('<b>{}</b><br/>unknown-mass instances'.format(mass['unknown_mass_instance_count']), ss['center'])]]
    ft = Table(facts, colWidths=[doc.width/4]*4)
    ft.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.5,GRID),
        ('INNERGRID',(0,0),(-1,-1),.5,colors.white),('TOPPADDING',(0,0),(-1,-1),7),
        ('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story += [ft, Spacer(1, 3*mm), p('This record provides the r10 assembly order, candidate seven-motor map, torque-off calibration checklist, revision-matched engineering screen and complete part-number index. It does not authorize fabrication, energizing, device-ID writes, motion tests or load tests.', ss['body']),
        p('Native source SHA256: <font name="Courier">{}</font>'.format(native_sha), ss['small']), PageBreak()]

    story += [p('1 | Architecture and source fidelity', ss['h1']),
        p('The candidate preserves the coupled two-output spine, seven physical motors and six commanded coordinates, four distinct fore/hind leg modules in the same sagittal orientation, four prescribed knee coordinates, S9 linkage topology, physical extension and compression springs, and bilateral hind cable route. The r10 center structure is one monolithic native cage, source FRM_LUMBAR_MONOLITHIC_CAGE_r09 with part number FRM_LUMBAR_MONOLITHIC_CAGE_r10, used once as LumbarIntegrated1. Integral fixed E beams and round-ended bearing lugs meet separate moving torso clevises. Fourteen separate pin, bearing, washer and retainer instances complete the assumed central stacks. Revised torso plate slots and four long B-C relieved bars retain the existing axes and motion ownership. Solid upper sagittal horn cheeks meet perpendicular windowed crosswalls, with the top open for carrier access. The former second half, four lumbar ties and eight associated tie screws are retired. The integral geometry has no assembly seam; its strength and print process remain unverified.', ss['body']),
        p('Movie S1 at 54-64 seconds supports the fixed central lug, separate moving slotted plate and broad relieved long-link morphology; its 51-second red skeleton is schematic. See docs/21_reference_fidelity_r10.md for retained frames and provenance. Dimensions remain reconstruction assumptions. Wall, window, relief and carrier access details are engineering adaptations represented by editable native features. All metric plate, clevis, central bearing stack and long-bar relief dimensions are DESIGN_ASSUMPTION. Supplier fits, tolerances, insertion access and strength remain unverified. Seven changed existing instances and fourteen new hardware instances require all 9996 affected pairs at 1346 exact states, alongside strict identity evidence for the other 466 instances.', ss['body'])]
    image_names = [('r10_robot_side.png', 'Assembled side view'), ('r10_spine_source_facing.png', 'Source-facing spine detail'),
                   ('r10_bare_lumbar_pos_y_oblique.png', 'Lumbar cage, positive-Y face'),
                   ('r10_bare_lumbar_neg_y_oblique.png', 'Lumbar cage, negative-Y face')]
    image_cells = []
    for name, caption in image_names:
        path = crop_image(name)
        image_cells.append((Image(str(path), width=(doc.width-8*mm)/2, height=(doc.width-8*mm)/2*.64), caption))
    griddata = []
    for i in (0, 2):
        griddata.append([image_cells[i][0], image_cells[i+1][0]])
        griddata.append([p(image_cells[i][1], ss['caption']), p(image_cells[i+1][1], ss['caption'])])
    grid = Table(griddata, colWidths=[(doc.width-8*mm)/2]*2)
    grid.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),
        ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    story += [Spacer(1, 2*mm), grid, p('Captures are actual FreeCAD views of saved r10 geometry; the paired oblique cage views expose opposite faces for source-fidelity inspection.', ss['caption'])]
    bbox = mass['actual_assembled_bbox_mm']
    ref = mass.get('reference_envelope_mm', {'X':110,'Y':99,'Z':84})
    story += [p('Saved envelope: {:.3f} x {:.3f} x {:.3f} mm; reference: {:.1f} x {:.1f} x {:.1f} mm. This comparison records the candidate packaging and does not imply scale conformity.'.format(
        bbox['x_mm'], bbox['y_mm'], bbox['z_mm'], ref['X'], ref['Y'], ref['Z']), ss['body']), PageBreak()]

    story += [p('Central attachment and revised profiles', ss['h1']),
        p('The fixed center beam/lug, moving torso clevises and plates, and relieved long B-C bars are separate functional classes. The views below identify the current proposal; every metric addition remains DESIGN_ASSUMPTION. Retained Movie S1 morphology does not establish dimensions, fits, material or strength.', ss['body'])]
    for left, right in ((('r10_central_attachment_bare.png', 'Fixed beam/lug and moving clevis'),
                         ('r10_long_bar_profile.png', 'Long B-C relief; four stable instances')),
                        (('r10_fore_plate_profile.png', 'Fore torso plate'),
                         ('r10_hind_plate_profile.png', 'Hind torso plate'))):
        cells = []
        for name, caption in (left, right):
            cells.append([Image(str(crop_image(name)), width=(doc.width-8*mm)/2,
                                height=(doc.width-8*mm)/2*.64), p(caption, ss['caption'])])
        panel = Table([[cells[0][0], cells[1][0]], [cells[0][1], cells[1][1]]],
                      colWidths=[(doc.width-8*mm)/2]*2)
        panel.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
        story += [panel, Spacer(1, 3*mm)]
    story += [p('Central hardware: two pins, four bearings, four washers and four retainers. Pins/washers/retainers follow the torso outputs; bearings belong to the fixed frame. The supplemental pin-access audit clears E1/E2 insertion from either Y side at 24 sampled stations per path only when both center retainers and the entry-side outer E journal and its two retainers are deferred. Install the center pin before those outer journals. Elastic clip installation, tool/service access, fits, bearing race retention, thrust and alignment remain unverified. See reports/verification/r10_central_pin_access.json.', ss['body']), PageBreak()]

    story += [p('2 | Assembly sequence', ss['h1'])]
    steps = [
        ('1. Stage exact parts', 'Use the r10 BOM and instance list. Record supplier identity, batch, material, finish, measured dimensions and mass. Preserve unknown mass explicitly.'),
        ('2. Build the spine core', 'Assemble A/B/C shafts, links, crank hardware, guides and liners at the native placements. Defer the entry-side outer E journals and their retainers until the center pins are installed in step 4. Retain both coupled outputs and the two XL motors. Check axial capture, free motion and tool access.'),
        ('3. Install the one-piece lumbar cage', 'Use the single saved LumbarIntegrated1 placement. Inspect solid horn cheeks, perpendicular windowed crosswalls, open top, native travel reliefs and carrier access. Do not install the retired second half, four FixedLumbarTie parts or eight FixedTieScrew parts. Verify process, wall quality and actual interfaces before fitting hardware.'),
        ('4. Fit torso structures and joints', 'Retain fixed E beams/lugs, separate moving fore/hind clevises and revised plates, and the four long B-C bars. Seat the central bearings/washers, insert each center pin along Y with its center retainers and entry-side outer E journal/retainers uninstalled, then fit the center retainers before the deferred outer E journal/retainers. The four sampled pin paths retain structural bodies, bearings, spacers and cables. Clip deformation/tool access, fits, thrust retention, coaxial alignment and physical assembly remain release blockers; retain existing E axes and S9 topology.'),
        ('5. Install motors and adapters', 'The two XL330-M077-T and five XC330-M181-T solids are 20 x 26 x 34 mm in native XYZ (catalog W/H/D 20 x 34 x 26 mm). Critical mount/output/horn/connector interfaces remain provisional. Confirm the real case pattern, output center, pilot/spline, horn pattern, fastener engagement, connectors and cable bend space from exact drawings or metrology.'),
        ('6. Assemble the four legs', 'Retain distinct fore/hind modules and the same +X-forward, +Y-left, +Z-up direction. Fit hip axes, three links, pins, bearings, spacers, clips and return features in their saved sides.'),
        ('7. Fit springs and cable drive', 'Identify spring rate/free length/end form/preload. Preserve passive hind knees and the bilateral cable path. Validate cable bend, grip, tension and slip on bench coupons before robot loading.'),
        ('8. Fit carrier and route harness', 'Carrier retainer outer wall is 0.8 mm after expansion to X=[-24.8,4.8] mm; board and screw locations are unchanged. Verify actual PCB population/connectors. Keep power and TTL wiring correct, strain-relieved and clear of moving parts.'),
        ('9. Torque-off inspection', 'With supply disconnected and torque off, inspect engagement, clips, hand motion, spring seats, cable paths, pinch points, polarity and plug access. Stop on binding or mismatch. This is a proposed sequence; no physical inspection has occurred.'),
    ]
    for title, body in steps:
        story.append(KeepTogether([p(title, ss['h2']), p(body, ss['body'])]))
    story += [p('Nominal interfaces are geometry candidates, not manufacturing tolerances', ss['h2'])]
    fit = [[p('Interface',ss['th']),p('Candidate nominal',ss['th']),p('Still to verify',ss['th'])],
        [p('Bearing seat',ss['td']),p('4.05 mm seat / 4.00 mm OD',ss['td']),p('Bearing type, process size, retention and wall strength',ss['td'])],
        [p('Journal / bore',ss['td']),p('1.90 mm journal / 2.00 mm bore',ss['td']),p('Actual shaft, finish, coaxiality and running fit',ss['td'])],
        [p('Remaining carrier clamp',ss['td']),p('2.50 mm bore / nominal 2.40 mm tie',ss['td']),p('Tie size, preload, friction, creep and retention',ss['td'])],
        [p('OpenRB carrier',ss['td']),p('25 x 66 mm board footprint; 0.8 mm retainer wall',ss['td']),p('Board thickness, populated keepouts, connectors and mount',ss['td'])]]
    story += [make_table(fit,[75,115,doc.width-190]), PageBreak()]

    story += [p('3 | Motor map and torque-off calibration', ss['h1']),
        p('The candidate map has seven motors and six commanded coordinates because the two spine motors share phase. It is not a commissioned device map. No IDs have been written, offsets measured, torque enabled or hardware moved.', ss['body'])]
    maprows = [[p('ID',ss['th']),p('Motor envelope',ss['th']),p('Candidate coordinate',ss['th'])]]
    mapentries = [('1','XL330-M077-T spine A','Shared spine phase theta'),('2','XL330-M077-T spine B','Same theta; redundant paired drive'),
        ('3','XC330-M181-T fore left','Fore-left hip/thigh'),('4','XC330-M181-T fore right','Fore-right hip/thigh'),
        ('5','XC330-M181-T hind left','Hind-left hip/thigh'),('6','XC330-M181-T hind right','Hind-right hip/thigh'),
        ('7','XC330-M181-T hind wheel','Bilateral tendon take-up')]
    for row in mapentries: maprows.append([p(x,ss['td']) for x in row])
    story += [make_table(maprows,[35,180,doc.width-215]), p('Record-only checklist for any later authorized commissioning',ss['h2'])]
    cal = [[p('Unit',ss['th']),p('Record before a separately authorized powered test',ss['th'])],
        [p('Each ID 1-7',ss['td']),p('Exact model/serial, output orientation, sign, mechanical reference, raw encoder, offset, software limits, current/temperature limits, operator and date.',ss['td'])],
        [p('Spine pair 1/2',ss['td']),p('Both mechanical references and unloaded tracking error; safe synchronization, torque sharing and stop limits.',ss['td'])],
        [p('Leg IDs 3-6',ss['td']),p('Verify the same positive sagittal direction at all four mounts; record each real motor sign.',ss['td'])],
        [p('Wheel ID 7',ss['td']),p('Verify both cable branch winding signs and record terminal retention evidence.',ss['td'])]]
    story += [make_table(cal,[76,doc.width-76]), p('The saved neutral pose does not establish encoder zero, spline orientation, hard stops, tendon preload or loaded spring equilibrium. Keep offsets unset and torque disabled until real interfaces and safe restraints are established. This document does not authorize energizing, ID writes, jogging, gait operation, cable pull or calibration motion.',ss['body']), PageBreak()]

    story += [p('4 | Mass and engineering demand screen', ss['h1']),
        p('Values below are loaded from the final r10 calculation files. Geometry masses use explicit material-class density estimates; nominal purchased mass metadata takes precedence. Unknown mass remains excluded from the known sum. Point-mass inertia omits each solid’s own centroidal inertia.',ss['body'])]
    known = screen['known_mass']; sensitivity = screen.get('assumed_loaded_sensitivity')
    mass_rows = [[p('Quantity',ss['th']),p('Known case',ss['th']),p('Separate sensitivity case',ss['th'])],
        [p('Mass',ss['td']),p('{:.4f} g'.format(known['mass_g']),ss['td']),p('{:.4f} g'.format(sensitivity['mass_g']) if sensitivity else 'Not reported',ss['td'])],
        [p('CoM X/Y/Z',ss['td']),p('({:.3f}, {:.3f}, {:.3f}) mm'.format(*known['center_mm']),ss['td']),p('({:.3f}, {:.3f}, {:.3f}) mm'.format(*sensitivity['center_mm']) if sensitivity else 'Not reported',ss['td'])],
        [p('Point-mass inertia diagonal Ixx/Iyy/Izz',ss['td']),p(' / '.join('{:.1f}'.format(known['point_mass_inertia_g_mm2'][i][i]) for i in range(3))+' g mm2',ss['td']),p(' / '.join('{:.1f}'.format(sensitivity['point_mass_inertia_g_mm2'][i][i]) for i in range(3))+' g mm2' if sensitivity else 'Not reported',ss['td'])]]
    story += [make_table(mass_rows,[108,doc.width*.39,doc.width*.61-108]),
        p('Actual B-rep envelope: {:.3f} x {:.3f} x {:.3f} mm. Density-based known sum: {:.4f} g; purchased mass: {:.4f} g; unknown-mass instances: {}. These are estimates, not physical weighing.'.format(
            mass['actual_assembled_bbox_mm']['x_mm'],mass['actual_assembled_bbox_mm']['y_mm'],mass['actual_assembled_bbox_mm']['z_mm'],
            mass['known_mass_sum_g'],mass['known_purchased_mass_g'],mass['unknown_mass_instance_count']),ss['body'])]
    cases = screen.get('load_screens',{}).get('cases',[])
    spine_cases = screen.get('load_screens',{}).get('spine_B_shaft',{}).get('cases',[])
    if cases:
        demand = [[p(x,ss['th']) for x in ('Alpha','Support','Fore hip N m','Hind hip N m','Pin shear MPa','Pin bend MPa','Seat MPa','B shaft MPa')]]
        for alpha in (1,3,6):
            for support,label in (('two_legs_equal_share','2-leg equal'),('one_leg_worst_case','1-leg worst')):
                fore=next(c for c in cases if c['alpha']==alpha and c['support']==support and c['leg']=='foreL')
                hind=next(c for c in cases if c['alpha']==alpha and c['support']==support and c['leg']=='hindL')
                spine=next(c for c in spine_cases if c['alpha']==alpha and c['support']==support)
                demand.append([p(str(alpha),ss['td']),p(label,ss['td']),p('{:.4f}'.format(fore['hip_static_moment_Nm']),ss['td']),
                    p('{:.4f}'.format(hind['hip_static_moment_Nm']),ss['td']),p('{:.2f}'.format(fore['pin_single_shear_MPa']),ss['td']),
                    p('{:.2f}'.format(fore['pin_nominal_bending_stress_MPa']),ss['td']),p('{:.2f}'.format(fore['PA12_bearing_seat_projected_pressure_MPa']),ss['td']),
                    p('{:.2f}'.format(spine['nominal_bending_stress_MPa']),ss['td'])])
        widths=[31,67,48,48,48,48,54,doc.width-344]
        story += [p('Quasi-static demand estimates',ss['h2']), make_table(demand,widths),
            p('The screen uses the load cases and geometry inputs in reports/verification/r10_engineering_screen.json. Pin bending is a simplified circular beam estimate; seat pressure is projected area only; B-shaft bending assumes a simply supported central point load and the report span. Loads, contact distribution, dynamics, cable forces and local failure modes are not solved. No strength, fatigue, creep, bearing, motor-duty or safety-factor pass is claimed.',ss['small'])]
        fore_worst=next(c for c in cases if c['alpha']==6 and c['support']=='one_leg_worst_case' and c['leg']=='foreL')
        hind_worst=next(c for c in cases if c['alpha']==6 and c['support']=='one_leg_worst_case' and c['leg']=='hindL')
        story.append(p('At the alpha 6 one-leg case, estimated hip moments are {:.0f}% fore and {:.0f}% hind of the cited XC330-M181-T stall torque at 5 V. Stall is not a continuous-duty or thermal limit.'.format(
            100*fore_worst['hip_moment_fraction_of_XC330_M181_T_stall_at_5V'],
            100*hind_worst['hip_moment_fraction_of_XC330_M181_T_stall_at_5V']),ss['body']))
    limitations = screen.get('limitations',[])
    if limitations:
        story += [p('Calculation limitations: '+ '; '.join(limitations),ss['small'])]
    story += [PageBreak(), p('5 | Verification boundary and unresolved interfaces',ss['h1'])]
    ver_rows = [[p('Gate',ss['th']),p('Final record',ss['th']),p('Scope',ss['th'])],
        [p('Neutral raw intersections',ss['td']),p(evidence['neutral'].get('status','UNKNOWN'),ss['td']),p('{} instances; prescribed pose only'.format(evidence['neutral'].get('instances','?')),ss['td'])],
        [p('Composite finite motion',ss['td']),p(evidence['motion']['status'],ss['td']),p('Historical r08 985 states + strict 466 unchanged identity + 9996 changed pairs at {} states; sampled only'.format(len(evidence['motion']['completed_sample_ids'])),ss['td'])],
        [p('AX0 / AX1',ss['td']),p(evidence['ax01']['AX0']+' / '+evidence['ax01']['AX1'],ss['td']),p('{} instances / {} source definitions / {} prescribed poses; no mesh/video or dynamics claim'.format(evidence['ax01']['physical_instances'],evidence['ax01']['source_definitions'],len(evidence['poses']['frames'])),ss['td'])],
        [p('STEP/package',ss['td']),p(evidence['package'].get('status','UNKNOWN'),ss['td']),p('Serialized geometry round trips; no fabrication release',ss['td'])],
        [p('Drawings',ss['td']),p(evidence['drawings'].get('visual_review','UNKNOWN'),ss['td']),p('{} sheets / {} dimensions'.format(evidence['drawings'].get('sheet_count','?'),evidence['drawings'].get('dimension_count','?')),ss['td'])],
        [p('Profiles',ss['td']),p(evidence['profiles'].get('status','UNKNOWN'),ss['td']),p('Native-derived flat-stock/profile readback',ss['td'])]]
    story += [make_table(ver_rows,[85,90,doc.width-175]),
        p('A finite sampled sweep does not prove continuous clearance, loaded equilibrium, endurance or hardware performance. Motor output/mount/horn/connector interfaces, OpenRB population and mounting, bearing/shaft/clip fits and retention, fastener thread and engagement, spring identity and preload, cable holding force, material/process allowables and physical load paths remain open. No fabrication release or physical build inspection is claimed.',ss['body']),
        p('Evidence identity',ss['h2']),
        p('Native: cad/flexor_r10_robot.FCStd (SHA256 {}). BOM: bom/bom_r10.csv and bom/instances_r10.csv. Package: reports/package_manifest_r10.json. Mass: reports/verification/r10_mass_envelope.json. Demand calculation: reports/verification/r10_engineering_screen.json. Neutral: reports/verification/r10_neutral.json. Motion: reports/verification/r10_changed_partitions/summary.json, freeze.json, identity.json and all changed-pair partitions, backed by reports/verification/r08_motion_partitions/full_summary.json. Animation interface: reports/animation/ax01_r10.json and animation/motion/ax01_r10.json. Drawings: drawings/r10/drawing_manifest_r10.json. Profiles: exports/profiles/r10/profile_manifest_r10.json.'.format(native_sha),ss['small']), PageBreak()]

    story += [p('Appendix A | Complete r10 part-number index',ss['h1']),
        p('All exact part numbers and aggregate quantities are read from bom/bom_r10.csv. The revision-specific CSV and instance list remain authoritative for roles, materials, provenance and individual placements.',ss['body'])]
    bomdata = [[p('Group',ss['th']),p('Exact part number',ss['th']),p('Qty',ss['th'])]]
    for row in rows:
        bomdata.append([p(category(row['part_number']),ss['td']),p(row['part_number'],ss['td']),p(row['quantity'],ss['td'])])
    story.append(LongTable(bomdata,colWidths=[112,doc.width-150,38],repeatRows=1,hAlign='LEFT',splitByRow=1,
        style=TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),NAVY),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.3,GRID),
            ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)])))
    story += [Spacer(1,5*mm),p('Appendix totals: {} unique part numbers, {} assembly instances. The OpenRB PCB mass remains whatever the matching r10 mass/BOM reports; do not substitute an assumed zero.'.format(len(rows),count),ss['body'])]
    doc.build(story)
    return {'pdf':str(OUT),'native_sha256':native_sha,'unique_part_numbers':len(rows),'assembly_instances':count}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-sha256', required=True, help='Explicit lead-frozen canonical r10 SHA256')
    args = parser.parse_args()
    print(json.dumps(build(args.native_sha256), indent=2))
