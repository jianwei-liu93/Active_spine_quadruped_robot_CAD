"""Build the r08 assembly and calibration PDF from final revision-matched evidence.

The generator deliberately refuses to publish a PDF until the frozen r08
package, native, motion, drawing, profile, mass and engineering-screen records
are present and pass their declared gates. It writes only the owned r08 PDF
and cropped copies of actual r08 FreeCAD captures.
"""
from __future__ import print_function

import csv
import hashlib
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
    Spacer, Table, TableStyle, Image, PageBreak, LongTable, KeepTogether)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/flexor_r08_assembly_calibration.pdf'
VIEW_DIR = ROOT / 'reports/views/manual_r08'
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
        'title': ParagraphStyle('r08title', parent=base['Title'], fontName='Helvetica-Bold',
            fontSize=27, leading=31, textColor=NAVY, spaceAfter=8),
        'subtitle': ParagraphStyle('r08subtitle', parent=base['Normal'], fontSize=12,
            leading=17, textColor=MID, spaceAfter=10),
        'h1': ParagraphStyle('r08h1', parent=base['Heading1'], fontName='Helvetica-Bold',
            fontSize=18, leading=22, textColor=NAVY, spaceAfter=8, keepWithNext=True),
        'h2': ParagraphStyle('r08h2', parent=base['Heading2'], fontName='Helvetica-Bold',
            fontSize=11.5, leading=14, textColor=TEAL, spaceBefore=8, spaceAfter=4, keepWithNext=True),
        'body': ParagraphStyle('r08body', parent=base['BodyText'], fontName='Helvetica',
            fontSize=8.7, leading=12, textColor=INK, spaceAfter=6),
        'small': ParagraphStyle('r08small', parent=base['BodyText'], fontName='Helvetica',
            fontSize=7.4, leading=9.5, textColor=INK, spaceAfter=3),
        'caption': ParagraphStyle('r08caption', parent=base['BodyText'], fontName='Helvetica-Oblique',
            fontSize=7.4, leading=9, textColor=MID, alignment=1, spaceBefore=3, spaceAfter=6),
        'th': ParagraphStyle('r08th', parent=base['BodyText'], fontName='Helvetica-Bold',
            fontSize=7.2, leading=9, textColor=colors.white, spaceAfter=0),
        'td': ParagraphStyle('r08td', parent=base['BodyText'], fontName='Helvetica',
            fontSize=7.2, leading=9, textColor=INK, spaceAfter=0),
        'center': ParagraphStyle('r08center', parent=base['BodyText'], fontName='Helvetica-Bold',
            fontSize=8, leading=10, textColor=NAVY, alignment=1),
    }


def p(text, style):
    return Paragraph(safe(text), style)


def read_json(rel, required=False):
    path = ROOT / rel
    if not path.exists():
        if required:
            raise RuntimeError('Required final r08 evidence is missing: ' + rel)
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def gate_evidence():
    required = {
        'package': 'reports/package_manifest_r08.json',
        'mass': 'reports/verification/r08_mass_envelope.json',
        'engineering': 'reports/verification/r08_engineering_screen.json',
        'neutral': 'reports/verification/r08_neutral.json',
        'motion': 'reports/verification/r08_motion_partitions/full_summary.json',
        'drawings': 'drawings/r08/drawing_manifest_r08.json',
        'profiles': 'exports/profiles/r08/profile_manifest_r08.json',
        'capture': 'reports/views/r08_capture_manifest.json',
    }
    data = {key: read_json(path, required=True) for key, path in required.items()}
    native = ROOT / 'cad/flexor_r08_robot.FCStd'
    native_sha = sha256(native)
    package = data['package']
    if package.get('revision') != 'r08' or package.get('status') != PACKAGE_STATUS:
        raise RuntimeError('r08 package manifest is not in the validated export state')
    expected_sha = (package.get('native_document') or {}).get('sha256')
    if expected_sha != native_sha:
        raise RuntimeError('package manifest native SHA does not match cad/flexor_r08_robot.FCStd')
    for key in ('mass', 'neutral', 'drawings', 'profiles', 'capture'):
        if data[key].get('revision') != 'r08':
            raise RuntimeError('{} record is not revision r08'.format(key))
    if data['motion'].get('stage') != 'full':
        raise RuntimeError('motion summary is not the full r08 run')
    if data['neutral'].get('status') != 'PASS':
        raise RuntimeError('r08 prescribed-pose raw-intersection check is not PASS')
    if data['motion'].get('status') != 'PASS':
        raise RuntimeError('r08 full native motion screen is not PASS')
    if data['drawings'].get('visual_review') != 'PASS' or data['drawings'].get('pdf_exports') not in ('PASS', 'COMPLETE'):
        raise RuntimeError('r08 drawing PDF export and visual review are not both PASS')
    if data['profiles'].get('status') not in ('PASS', 'PASS_EXACT_PROFILE_READBACK'):
        raise RuntimeError('r08 profile round-trip check is not PASS')
    if data['capture'].get('visual_review') != 'PASS':
        raise RuntimeError('r08 source-fidelity image review is not PASS')
    if data['mass'].get('status') != 'COMPUTED_FROM_DOCUMENT':
        raise RuntimeError('r08 mass report is not a completed document calculation')
    if data['engineering'].get('native_document') != str(native):
        raise RuntimeError('r08 engineering screen does not identify the final native document')
    for key in ('mass', 'engineering', 'neutral', 'motion', 'drawings', 'profiles'):
        recorded = (data[key].get('native_sha256') or data[key].get('canonical_robot_sha256')
                    or data[key].get('source_sha256'))
        if recorded and recorded != native_sha:
            raise RuntimeError('{} report native SHA does not match final r08 candidate'.format(key))
    if package.get('physical_link_count') != data['mass'].get('instance_count'):
        raise RuntimeError('package and mass report instance counts disagree')
    if package.get('bom_mass_summary', {}).get('part_number_count') != data['mass'].get('part_number_count'):
        raise RuntimeError('package and mass report part-number counts disagree')
    return data, native_sha


def bom_rows():
    path = ROOT / 'bom/bom_r08.csv'
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise RuntimeError('bom/bom_r08.csv has no part rows')
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
        raise RuntimeError('Required r08 FreeCAD capture is missing: ' + str(source))
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
    canvas.drawString(19 * mm, PAGE_H - 10.5 * mm, 'FLEXOR-F INSPIRED QUADRUPED | R08')
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


def build():
    evidence, native_sha = gate_evidence()
    rows = bom_rows()
    mass = evidence['mass']
    screen = evidence['engineering']
    summary = evidence['package']['bom_mass_summary']
    if len(rows) != mass['part_number_count']:
        raise RuntimeError('r08 BOM row count disagrees with final mass report')
    count = sum(int(r['quantity']) for r in rows)
    if count != mass['instance_count']:
        raise RuntimeError('r08 BOM quantities disagree with final mass report')
    ss = styles()
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=19*mm, rightMargin=19*mm,
        topMargin=19*mm, bottomMargin=19*mm, title='FLEXOR r08 Assembly and Calibration Record',
        author='Engineering review package', subject='Editable review candidate; no fabrication release')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
        leftPadding=0, rightPadding=0, topPadding=1*mm, bottomPadding=1*mm, id='main')
    doc.addPageTemplates([PageTemplate(id='all', frames=[frame], onPage=header_footer)])
    story = []

    # Candidate cover and actual captured assembly views.
    hero = crop_image('r08_robot_assembled.png')
    story += [Spacer(1, 7*mm), p('Assembly &amp; calibration<br/>record', ss['title']),
        p('Review candidate r08 | FLEXOR-F inspired active-spine quadruped', ss['subtitle'])]
    status = Table([[p('EDITABLE CANDIDATE', ss['center']), p('PROVISIONAL INTERFACES', ss['center']),
                     p('NOT FOR FABRICATION', ss['center'])]], colWidths=[doc.width/3]*3)
    status.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE_ORANGE),('BOX',(0,0),(-1,-1),.7,ORANGE),
        ('INNERGRID',(0,0),(-1,-1),.4,colors.white),('TOPPADDING',(0,0),(-1,-1),7),
        ('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story += [status, Spacer(1, 4*mm), Image(str(hero), width=doc.width, height=doc.width*.55),
        p('Actual saved FreeCAD view of the r08 candidate. Motor and controller representations are envelopes; this is not a photograph or supplier-interface verification.', ss['caption'])]
    facts = [[p('<b>{}</b><br/>physical links'.format(count), ss['center']),
              p('<b>{}</b><br/>unique part numbers'.format(len(rows)), ss['center']),
              p('<b>{:.3f} g</b><br/>known mass'.format(mass['known_mass_sum_g']), ss['center']),
              p('<b>{}</b><br/>unknown-mass instances'.format(mass['unknown_mass_instance_count']), ss['center'])]]
    ft = Table(facts, colWidths=[doc.width/4]*4)
    ft.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.5,GRID),
        ('INNERGRID',(0,0),(-1,-1),.5,colors.white),('TOPPADDING',(0,0),(-1,-1),7),
        ('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story += [ft, Spacer(1, 3*mm), p('This record provides the r08 assembly order, candidate seven-motor map, torque-off calibration checklist, revision-matched engineering screen and complete part-number index. It does not authorize fabrication, energizing, device-ID writes, motion tests or load tests.', ss['body']),
        p('Native source SHA256: <font name="Courier">{}</font>'.format(native_sha), ss['small']), PageBreak()]

    story += [p('1 | Architecture and source fidelity', ss['h1']),
        p('The candidate preserves the coupled two-output spine, seven physical motors and six commanded coordinates, four distinct fore/hind leg modules, S9 linkage topology, physical extension and compression springs, and bilateral hind cable route. The r08 center structure is two separate half-cages. Each has a solid upper sagittal horn cheek and two perpendicular windowed crosswalls, with the top open for carrier access. The two halves have 0.2 mm total seam clearance and are retained by the existing four transverse ties; the seam is nonstructural and no moment transfer is credited.', ss['body']),
        p('Movie S1 at 51.5 and 52.7 seconds supports the orthogonal crosswall and solid upper cheek arrangement. Dimensions remain reconstruction assumptions. Ø2.6 mm crosswall tie passages and carrier access pockets are engineering adaptations. The pockets add 2 mm provisional upper height while preserving a 1.85 mm top rail. Existing S9 pivots, shaft stacks, ties, liners and motor datums remain unchanged.', ss['body'])]
    image_names = [('r08_robot_side.png', 'Assembled side view'), ('r08_spine_source_facing.png', 'Source-facing spine detail'),
                   ('r08_bare_lumbar_pos_y_oblique.png', 'Lumbar cage, positive-Y face'),
                   ('r08_bare_lumbar_neg_y_oblique.png', 'Lumbar cage, negative-Y face')]
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
    story += [Spacer(1, 2*mm), grid, p('Captures are actual FreeCAD views of saved r08 geometry; the paired oblique cage views expose opposite faces for source-fidelity inspection.', ss['caption'])]
    bbox = mass['actual_assembled_bbox_mm']
    ref = mass.get('reference_envelope_mm', {'X':110,'Y':99,'Z':84})
    story += [p('Saved envelope: {:.3f} x {:.3f} x {:.3f} mm; reference: {:.1f} x {:.1f} x {:.1f} mm. This comparison records the candidate packaging and does not imply scale conformity.'.format(
        bbox['x_mm'], bbox['y_mm'], bbox['z_mm'], ref['X'], ref['Y'], ref['Z']), ss['body']), PageBreak()]

    story += [p('2 | Assembly sequence', ss['h1'])]
    steps = [
        ('1. Stage exact parts', 'Use the r08 BOM and instance list. Record supplier identity, batch, material, finish, measured dimensions and mass. Preserve unknown mass explicitly.'),
        ('2. Build the spine core', 'Assemble A/B/C shafts, links, crank hardware, guides, liners and retainers at the native placements. Retain both coupled outputs and the two XL motors. Check axial capture, free motion and tool access.'),
        ('3. Install both half-cages', 'Orient by the saved AppLinks. Verify solid upper cheeks, perpendicular windowed crosswalls, Ø2.6 tie passages, open top and carrier access. Keep the 0.2 mm seam open; no bond or bending transfer is assumed. The existing four ties retain the assembly.'),
        ('4. Fit torso structures and joints', 'Preserve distinct fore/hind structures, moving-frame axes and S9 topology. Verify shafts, journals, bearing stacks, ties and shims in their saved orientations.'),
        ('5. Install motors and adapters', 'Motor solids are case envelopes. Confirm the real case pattern, output center, pilot/spline, horn pattern, fastener engagement, connectors and cable bend space from exact drawings or metrology.'),
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
        [p('Tie clamp',ss['td']),p('2.50 mm bore / nominal 2.40 mm tie',ss['td']),p('Tie size, preload, friction, creep and retention',ss['td'])],
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
        p('Values below are loaded from the final r08 calculation files. Geometry masses use explicit material-class density estimates; nominal purchased mass metadata takes precedence. Unknown mass remains excluded from the known sum. Point-mass inertia omits each solid’s own centroidal inertia.',ss['body'])]
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
            p('The screen uses the load cases and geometry inputs in reports/verification/r08_engineering_screen.json. Pin bending is a simplified circular beam estimate; seat pressure is projected area only; B-shaft bending assumes a simply supported central point load and the report span. Loads, contact distribution, dynamics, cable forces and local failure modes are not solved. No strength, fatigue, creep, bearing, motor-duty or safety-factor pass is claimed.',ss['small'])]
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
        [p('Full native motion',ss['td']),p(evidence['motion'].get('status','UNKNOWN'),ss['td']),p('{} / {} states; finite sampled trajectories'.format(evidence['motion'].get('records_found','?'),evidence['motion'].get('samples_expected','?')),ss['td'])],
        [p('STEP/package',ss['td']),p(evidence['package'].get('status','UNKNOWN'),ss['td']),p('Serialized geometry round trips; no fabrication release',ss['td'])],
        [p('Drawings',ss['td']),p(evidence['drawings'].get('visual_review','UNKNOWN'),ss['td']),p('{} sheets / {} dimensions'.format(evidence['drawings'].get('sheet_count','?'),evidence['drawings'].get('dimension_count','?')),ss['td'])],
        [p('Profiles',ss['td']),p(evidence['profiles'].get('status','UNKNOWN'),ss['td']),p('Native-derived flat-stock/profile readback',ss['td'])]]
    story += [make_table(ver_rows,[85,90,doc.width-175]),
        p('A finite sampled sweep does not prove continuous clearance, loaded equilibrium, endurance or hardware performance. Motor output/mount/horn/connector interfaces, OpenRB population and mounting, bearing/shaft/clip fits, spring identity and preload, cable holding force, material/process allowables and physical load paths remain open. No fabrication release or physical build inspection is claimed.',ss['body']),
        p('Evidence identity',ss['h2']),
        p('Native: cad/flexor_r08_robot.FCStd (SHA256 {}). BOM: bom/bom_r08.csv and bom/instances_r08.csv. Package: reports/package_manifest_r08.json. Mass: reports/verification/r08_mass_envelope.json. Demand calculation: reports/verification/r08_engineering_screen.json. Neutral: reports/verification/r08_neutral.json. Motion: reports/verification/r08_motion_partitions/full_summary.json and matching manifest. Drawings: drawings/r08/drawing_manifest_r08.json. Profiles: exports/profiles/r08/profile_manifest_r08.json.'.format(native_sha),ss['small']), PageBreak()]

    story += [p('Appendix A | Complete r08 part-number index',ss['h1']),
        p('All exact part numbers and aggregate quantities are read from bom/bom_r08.csv. The revision-specific CSV and instance list remain authoritative for roles, materials, provenance and individual placements.',ss['body'])]
    bomdata = [[p('Group',ss['th']),p('Exact part number',ss['th']),p('Qty',ss['th'])]]
    for row in rows:
        bomdata.append([p(category(row['part_number']),ss['td']),p(row['part_number'],ss['td']),p(row['quantity'],ss['td'])])
    story.append(LongTable(bomdata,colWidths=[112,doc.width-150,38],repeatRows=1,hAlign='LEFT',splitByRow=1,
        style=TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),NAVY),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.3,GRID),
            ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)])))
    story += [Spacer(1,5*mm),p('Appendix totals: {} unique part numbers, {} assembly instances. The OpenRB PCB mass remains whatever the matching r08 mass/BOM reports; do not substitute an assumed zero.'.format(len(rows),count),ss['body'])]
    doc.build(story)
    return {'pdf':str(OUT),'native_sha256':native_sha,'unique_part_numbers':len(rows),'assembly_instances':count}


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
