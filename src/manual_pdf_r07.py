"""Build the r07 review assembly/calibration PDF from the project records.

This script only reads the native-candidate evidence, source docs, BOM and
actual FreeCAD screenshots. It writes the explicitly owned PDF and cropped
presentation copies under reports/views/manual_r07/.
"""
from __future__ import print_function
import csv
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
    Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, LongTable)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/flexor_r07_assembly_calibration.pdf'
VIEW_DIR = ROOT / 'reports/views/manual_r07'
PAGE_W, PAGE_H = A4
NAVY = colors.HexColor('#173247')
TEAL = colors.HexColor('#18838B')
ORANGE = colors.HexColor('#D16C43')
PALE = colors.HexColor('#EDF4F5')
PALE_ORANGE = colors.HexColor('#FFF1E9')
INK = colors.HexColor('#243642')
MID = colors.HexColor('#5A6B75')
GRID = colors.HexColor('#D1DDE1')


def ascii_safe(s):
    """Keep stable, searchable ASCII typography in the PDF."""
    if not isinstance(s, str):
        s = str(s)
    return (s.replace('\u2013', '-').replace('\u2014', '-').replace('\u2212', '-')
             .replace('\u00d7', 'x').replace('\u00d8', 'dia.')
             .replace('\u00b0', ' deg').replace('\u00b7', ' ')
             .replace('\u2264', '<=').replace('\u2265', '>='))


def para(text, style):
    return Paragraph(ascii_safe(text), style)


def styles():
    ss = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('ManualTitle', parent=ss['Title'], fontName='Helvetica-Bold',
            fontSize=27, leading=31, textColor=NAVY, spaceAfter=8),
        'subtitle': ParagraphStyle('ManualSub', parent=ss['Normal'], fontName='Helvetica',
            fontSize=12, leading=17, textColor=MID, spaceAfter=10),
        'h1': ParagraphStyle('ManualH1', parent=ss['Heading1'], fontName='Helvetica-Bold',
            fontSize=18, leading=22, textColor=NAVY, spaceBefore=1, spaceAfter=8,
            keepWithNext=True),
        'h2': ParagraphStyle('ManualH2', parent=ss['Heading2'], fontName='Helvetica-Bold',
            fontSize=11.5, leading=14, textColor=TEAL, spaceBefore=9, spaceAfter=4,
            keepWithNext=True),
        'body': ParagraphStyle('ManualBody', parent=ss['BodyText'], fontName='Helvetica',
            fontSize=8.7, leading=12, textColor=INK, spaceAfter=6),
        'small': ParagraphStyle('ManualSmall', parent=ss['BodyText'], fontName='Helvetica',
            fontSize=7.5, leading=10, textColor=INK, spaceAfter=3),
        'caption': ParagraphStyle('ManualCaption', parent=ss['BodyText'], fontName='Helvetica-Oblique',
            fontSize=7.4, leading=9, textColor=MID, alignment=TA_CENTER, spaceBefore=3, spaceAfter=7),
        'table': ParagraphStyle('ManualTable', parent=ss['BodyText'], fontName='Helvetica',
            fontSize=7.2, leading=9, textColor=INK, spaceAfter=0),
        'table_bold': ParagraphStyle('ManualTableBold', parent=ss['BodyText'], fontName='Helvetica-Bold',
            fontSize=7.3, leading=9, textColor=NAVY, spaceAfter=0),
        'table_head': ParagraphStyle('ManualTableHead', parent=ss['BodyText'], fontName='Helvetica-Bold',
            fontSize=7.3, leading=9, textColor=colors.white, spaceAfter=0),
        'callout': ParagraphStyle('ManualCallout', parent=ss['BodyText'], fontName='Helvetica-Bold',
            fontSize=9.4, leading=13, textColor=NAVY, spaceAfter=0),
        'center': ParagraphStyle('ManualCenter', parent=ss['BodyText'], fontName='Helvetica-Bold',
            fontSize=8, leading=10, textColor=NAVY, alignment=TA_CENTER),
    }


def make_actual_image(name):
    from PIL import Image as PILImage
    src = ROOT / 'reports/views' / name
    VIEW_DIR.mkdir(parents=True, exist_ok=True)
    out = VIEW_DIR / (src.stem + '_crop.png')
    im = PILImage.open(src).convert('RGB')
    w, h = im.size
    # Crop FreeCAD's application margins and navigation cube, retaining the
    # entire modeled assembly in the center of its actual screenshot.
    box = (int(w*.08), int(h*.08), int(w*.91), int(h*.92))
    im.crop(box).save(out, optimize=True)
    return out


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(.5)
    canvas.line(19*mm, PAGE_H-13*mm, PAGE_W-19*mm, PAGE_H-13*mm)
    canvas.setFillColor(NAVY)
    canvas.setFont('Helvetica-Bold', 7.5)
    canvas.drawString(19*mm, PAGE_H-10.5*mm, 'FLEXOR-F INSPIRED QUADRUPED | R07')
    canvas.setFillColor(ORANGE)
    canvas.drawRightString(PAGE_W-19*mm, PAGE_H-10.5*mm, 'REVIEW CANDIDATE - NOT FOR FABRICATION')
    canvas.setStrokeColor(GRID)
    canvas.line(19*mm, 14*mm, PAGE_W-19*mm, 14*mm)
    canvas.setFillColor(MID)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(19*mm, 9.5*mm, 'Assembly and torque-off calibration record | 2026-10-12')
    canvas.drawRightString(PAGE_W-19*mm, 9.5*mm, 'Page %d' % doc.page)
    canvas.restoreState()


def table(data, widths, repeat=1, font=7.2, header=True, padd=4, row_bgs=None):
    t = Table(data, colWidths=widths, repeatRows=repeat if header else 0, hAlign='LEFT')
    commands = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), padd), ('RIGHTPADDING', (0, 0), (-1, -1), padd),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), .35, GRID),
    ]
    if header:
        commands.extend([('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')])
    for ri, col in enumerate(row_bgs or [], start=1 if header else 0):
        commands.append(('BACKGROUND', (0, ri), (-1, ri), col))
    t.setStyle(TableStyle(commands))
    return t


def category(pn):
    if pn.startswith('DYNAMIXEL_'):
        return 'Actuators'
    if pn.startswith(('SPN_', 'SPINE_', 'DIRECT_CRANK_', 'G_CRANK_', 'GUIDE_COPPER', 'HORN_', 'JOURNAL_D1p9_L8')):
        return 'Spine drive and joints'
    if pn.startswith(('FRM_', 'TORSO_FORE_', 'TORSO_HIND_', 'FIXED_TIE_', 'MOTOR_CENTER_')):
        return 'Frames and fixed ties'
    if pn.startswith(('OpenRB150_', 'OPENRB150_')):
        return 'Controller board and carrier'
    if pn.startswith(('LEG_r02_fore', 'LEG_r02_hind', 'LEG_r02_COMPRESSION', 'LEG_r02_COMP_', 'KNEE_', 'TENDON_')):
        return 'Springs and hind tendon drive'
    if pn.startswith(('A_OUTER_', 'BRG_', 'LEG_r02_BRG_', 'RETAINING_', 'SPACER_')):
        return 'Bearings, clips and spacers'
    return 'Legs, pivots and output hardware'


def bom_rows():
    with (ROOT/'bom/bom_r07.csv').open(newline='') as f:
        return sorted([(category(r['part_number']), r['part_number'], int(r['quantity']))
                       for r in csv.DictReader(f)], key=lambda x:(x[0],x[1]))


def build():
    ss = styles()
    mass = json.loads((ROOT/'reports/verification/r07_mass_envelope.json').read_text())
    screen = json.loads((ROOT/'reports/verification/r07_engineering_screen.json').read_text())
    known = screen['known_mass']
    sensitivity = screen['assumed_loaded_sensitivity']
    cases = screen['load_screens']['cases']
    spine_cases = screen['load_screens']['spine_B_shaft']['cases']
    bom = bom_rows()
    if len(bom) != mass['part_number_count']:
        raise ValueError('BOM row count and saved r07 mass report disagree')
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=19*mm, rightMargin=19*mm,
        topMargin=19*mm, bottomMargin=19*mm, title='FLEXOR r07 Assembly and Calibration Record',
        author='Engineering review package', subject='Provisional review candidate; no hardware operation authorized')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
        leftPadding=0, rightPadding=0, topPadding=1*mm, bottomPadding=1*mm, id='main')
    doc.addPageTemplates([PageTemplate(id='all', frames=[frame], onPage=header_footer)])
    story = []

    # Cover page with an actual native FreeCAD capture.
    hero = make_actual_image('r07_robot_assembled.png')
    story += [Spacer(1, 7*mm), para('Assembly &amp; calibration<br/>record', ss['title']),
        para('Review candidate r07 | FLEXOR-F inspired active-spine quadruped', ss['subtitle'])]
    status = Table([[para('REVIEW CANDIDATE', ss['center']),
        para('PROVISIONAL INTERFACES', ss['center']),
        para('NO HARDWARE OPERATION AUTHORIZED', ss['center'])]], colWidths=[doc.width/3]*3)
    status.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE_ORANGE),('BOX',(0,0),(-1,-1),.7,ORANGE),
        ('INNERGRID',(0,0),(-1,-1),.4,colors.white),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story += [status, Spacer(1, 5*mm), Image(str(hero), width=doc.width, height=doc.width*0.565),
        para('Actual saved FreeCAD view of the r07 candidate. Motor and OpenRB blocks are envelopes; this image does not establish supplier mount or output datums.', ss['caption'])]
    summary = [
        [para('<b>486</b><br/>physical links', ss['center']), para('<b>105</b><br/>BOM part numbers', ss['center']),
         para('<b>{:.3f} g</b><br/>known nominal mass'.format(known['mass_g']), ss['center']),
         para('<b>1</b><br/>unknown-mass board', ss['center'])]
    ]
    t = Table(summary, colWidths=[doc.width/4]*4)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.5,GRID),
        ('INNERGRID',(0,0),(-1,-1),.5,colors.white),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story += [t, Spacer(1, 3*mm), para('This document describes the saved candidate, a practical assembly order, a proposed six-coordinate motor map, a torque-off calibration record, nominal demand screens and every BOM part number. It does not authorize fabrication, energizing, device-ID writes, motion tests or load tests.', ss['body']), PageBreak()]

    # Architecture and source-fidelity context.
    story += [para('1 | Architecture and source fidelity', ss['h1']),
        para('The modeled FLEXOR-F inspired candidate uses two XL330-M077-T motors redundantly driving one spine phase, four XC330-M181-T proximal leg motors and one XC330-M181-T hind-knee wheel motor. Six coordinates are commanded: one shared spine phase, four hip/thigh coordinates and one hind tendon-wheel coordinate. Foreleg elbow behavior and hind knees remain passive in the model. The assembly keeps the coupled two-output spine, three-segment limbs, paired hind cable route, and separate extension/compression spring representations.', ss['body']),
        para('Source basis and interpretation', ss['h2']),
        para('The main paper (pp. 4 and 16) and supplement (Table S1, p. 65) establish the broad actuator count and mechanism topology; Movie S1 (51-80 s) establishes visible arrangement and morphology, not precision dimensions. The r06-to-r07 frame interpretation follows the animation: a rounded lower lumbar opening, an upper window, local end shelves, short bearing ears, and distinct fore/hind transverse torso plates. Numeric cradle, plate, hole, fit, bracket and support dimensions are reconstruction assumptions unless separately supplier-verified. The current r07 supplier review confirms that exact motor mounting/output/horn and populated OpenRB interfaces remain unresolved. Source registry and frame interpretation: docs/01_reference_evidence.md and docs/13_candidate_frames_r06.md.', ss['body'])]
    img_grid = []
    for filename, caption in [('r07_robot_side.png','Assembled side view'),
                              ('r07_spine_torso_frames.png','Spine and torso frames'),
                              ('r07_bare_lumbar.png','Lumbar cradle/window'),
                              ('r07_spine_source_facing.png','Source-facing spine detail')]:
        im = make_actual_image(filename)
        img_grid.append((Image(str(im), width=(doc.width-10*mm)/2, height=(doc.width-10*mm)/2*.69), caption))
    cells=[]
    for i in (0,2):
        cells.append([img_grid[i][0], img_grid[i+1][0]])
        cells.append([para(img_grid[i][1],ss['caption']), para(img_grid[i+1][1],ss['caption'])])
    grid=Table(cells,colWidths=[(doc.width-10*mm)/2]*2)
    grid.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),
        ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    story += [grid, para('Screenshots are actual FreeCAD captures of saved r07 parts and placements. They are not photographs of a built robot.', ss['caption']),
        para('Scale and envelope comparison', ss['h2']),
        para('Native B-rep bounds are %.4f x %.1f x %.4f mm versus the 110 x 99 x 84 mm reference (+%.4f, +%.4f, +%.4f mm). Preserve the mismatch for design review; do not scale the assembly to force a match.' % (
            mass['actual_assembled_bbox_mm']['x_mm'],mass['actual_assembled_bbox_mm']['y_mm'],mass['actual_assembled_bbox_mm']['z_mm'],
            mass['actual_minus_reference_mm']['x_delta_mm'],mass['actual_minus_reference_mm']['y_delta_mm'],mass['actual_minus_reference_mm']['z_delta_mm']),ss['body']), PageBreak()]

    # Assembly process, split over pages.
    story += [para('2 | Assembly sequence', ss['h1']),
        para('Follow the saved native part placements and the exact PN list in Appendix A. Record measured purchase-part identity and dimensions before finalizing any mating part.',ss['body'])]
    steps1=[
        ('1. Stage and inspect parts','Match items by exact BOM part number. Record vendor code, batch, material, coating, measured dimensions and mass. Keep the controller mass unknown until verified.'),
        ('2. Build the spine core','Assemble A/B/C shaft families, native links, cranks, copper guides/liners and retainers in the saved arrangement. Preserve both coupled outputs and the two-motor spine drive. Check axial capture, free motion and tool access by inspection.'),
        ('3. Fit lumbar and torso frames','Install left/right rounded lumbar cradles and fore/hind transverse torso frames. Retain the saved shaft and tie topology. Do not substitute a flat center plate or add hardware at unmodeled positions. Inspect the upper window, lower opening, local shelves and guide ears.'),
        ('4. Install spine motors and adapters','Locate the XL case envelopes as modeled. Mate horns/cranks only after matching the exact motor output drawing or measuring a sample. Verify output center, spline, retaining screw, case holes and screw engagement independently.'),
        ('5. Assemble four legs','Keep all leg frames in the model convention: +X forward, +Y left, +Z up. Fit hip axes, three segment bodies, pins, bearings, spacers, clips and return features in the saved side. Fore/hind lengths differ; left/right retain the same sagittal angle convention.'),
    ]
    for title, text in steps1:
        story.append(KeepTogether([para(title,ss['h2']),para(text,ss['body'])]))
    story += [PageBreak(), para('2 | Assembly sequence (continued)',ss['h1'])]
    steps2=[
        ('6. Fit springs and hind tendon drive','Install one extension and one compression spring per leg with actual free length, rate, end form and preload recorded. Keep hind knees passive in the model. Seat each cable at its positive-capture feature; validate cable construction, clamp pressure, bend radius, tension retention and end slip on separate coupons before loading.'),
        ('7. Fit controller carrier','Place the OpenRB envelope in the free-edge tray, add the edge retainers and close both split clamps around the existing nominal 2.4 mm fixed ties. The 2.5 mm bore gives 0.10 mm nominal diametral clearance; clamp preload, friction, creep and retention are not qualified. Do not drill or assume PCB holes.'),
        ('8. Route harnesses and inspect service access','Route a separate TTL daisy-chain and external power harness with chassis strain relief and service loops clear of shafts, springs, tendons, bearings and clips. Use actual connector/cable dimensions. Check plug access and removable retainers.'),
        ('9. No-power mechanical inspection','With torque off and external supply disconnected, inspect fastener engagement, clip seating, free joint movement where possible, spring seating, cable paths, pinch points, polarity labels and connector clearance. Stop at binding or mismatch. This is a proposed inspection order; physical hardware inspection has not occurred.'),
    ]
    for title,text in steps2:
        story.append(KeepTogether([para(title,ss['h2']),para(text,ss['body'])]))
    story += [para('Nominal stackups to check against real parts',ss['h2'])]
    fit_rows=[
        [para('Interface',ss['table_head']),para('Nominal stack / result',ss['table_head']),para('Unresolved',ss['table_head'])],
        [para('Bearing seat',ss['table']),para('4.05 mm seat / 4.00 mm bearing OD = 0.05 mm diametral clearance',ss['table']),para('Vendor bearing type, tolerance and process size',ss['table'])],
        [para('Shaft/bearing bore',ss['table']),para('1.90 mm shaft / 2.00 mm bore = 0.10 mm diametral clearance',ss['table']),para('Shaft finish, coaxiality and running fit',ss['table'])],
        [para('Controller tie clamp',ss['table']),para('2.50 mm clamp bore / 2.40 mm tie OD = 0.10 mm clearance',ss['table']),para('Preload, seating friction, creep and retention',ss['table'])],
        [para('PCB edge tray',ss['table']),para('Board 25 x 66 x 1.6 mm; tray 28 x 70 mm; 1.5 mm nominal each side',ss['table']),para('Board thickness and component-free edges assumed; population volume reserved separately',ss['table'])],
    ]
    story += [table(fit_rows,[90,185,doc.width-275],font=7.2), PageBreak()]

    # Controller map and no-operation constraint.
    story += [para('3 | Controller map and torque-off calibration record',ss['h1']),
        para('The following is a proposed logical ID map only. No IDs were written, no servo offsets measured, and no powered test or hardware movement was performed.',ss['body'])]
    maprows=[[para('Candidate ID',ss['table_head']),para('Device',ss['table_head']),para('Commanded coordinate',ss['table_head'])]]
    entries=[('1','XL330-M077-T spine motor A','Shared spine phase theta'),('2','XL330-M077-T spine motor B','Same theta; redundant pair'),
        ('3','XC330-M181-T fore left','Fore-left hip/thigh'),('4','XC330-M181-T fore right','Fore-right hip/thigh'),
        ('5','XC330-M181-T hind left','Hind-left hip/thigh'),('6','XC330-M181-T hind right','Hind-right hip/thigh'),
        ('7','XC330-M181-T hind tendon wheel','Bilateral tendon take-up')]
    for row in entries: maprows.append([para(x,ss['table']) for x in row])
    story += [table(maprows,[72,185,doc.width-257],row_bgs=[colors.white,PALE,colors.white,PALE,colors.white,PALE,colors.white]),
        para('Six commands result because IDs 1 and 2 share one spine coordinate. Foreleg passive motion and both hind knees remain passive. The left/right legs use the same modeled positive sagittal direction; record any real motor sign inversion per ID instead of changing the model convention.',ss['body']),
        para('Power interface hold point',ss['h2']),
        para('Candidate bench architecture: regulated external 5 V rail, TTL half-duplex bus and common ground. Confirm the OpenRB input, motor-rail separation, current capacity, connector pinout and USB back-feed from official documentation before connecting. USB is not a motor power supply. This document does not authorize energizing, device-ID writes, torque enable, jogging, a gait run, cable pull or calibration motion.',ss['body']),
        para('Record-only calibration checklist (torque off)',ss['h2'])]
    cal_rows=[[para('ID / pair',ss['table_head']),para('Record before any later authorized commissioning',ss['table_head'])],
        [para('Each ID 1-7',ss['table']),para('Exact model and serial; measured output-to-link orientation; direction sign; constrained reference; raw encoder reading; selected offset; software limits; current/temperature limits; operator and date.',ss['table'])],
        [para('Spine pair 1/2',ss['table']),para('Record both mechanical references and unloaded tracking error. Establish safe tracking, torque-sharing and stop limits before enable.',ss['table'])],
        [para('Leg IDs 3-6',ss['table']),para('Verify the same positive sagittal direction at all four mounts and record each installation sign.',ss['table'])],
        [para('Wheel ID 7',ss['table']),para('Verify winding sign independently for both cable branches and record terminal retention evidence.',ss['table'])]]
    story += [table(cal_rows,[100,doc.width-100]),
        para('Saved neutral pose is a software reference only; it does not establish encoder zero, spline tooth orientation, mechanical stop, tendon preload or loaded spring equilibrium. Leave offsets/signs unset and torque disabled at startup until actual parts and safe constraints are identified.',ss['body']), PageBreak()]

    # Mass/load screen.
    story += [para('4 | Mass, center of mass and inertia estimate',ss['h1']),
        para('Read-only FreeCAD calculation from the saved 486-link assembly; each link mass comes from nominal PurchasedMass_g or B-rep volume times the r07 material density estimate. The point-mass inertia omits each solid\'s own centroidal inertia.',ss['body'])]
    known_com='({:.4f}, {:.4f}, {:.4f}) mm'.format(*known['center_mm'])
    loaded_com='({:.4f}, {:.4f}, {:.4f}) mm'.format(*sensitivity['center_mm'])
    known_i=known['point_mass_inertia_g_mm2']
    loaded_i=sensitivity['point_mass_inertia_g_mm2']
    fmt_tensor=lambda a: '[{}]'.format(', '.join('[{}]'.format(', '.join('{:.2f}'.format(x) for x in row)) for row in a))
    fmt_diag=lambda a: ' / '.join('{:.2f}'.format(a[i][i]) for i in range(3))
    mr=[[para('Quantity',ss['table_head']),para('Known mass case',ss['table_head']),para('Separate sensitivity case',ss['table_head'])],
        [para('Mass',ss['table']),para('{:.4f} g'.format(known['mass_g']),ss['table']),para('{:.4f} g'.format(sensitivity['mass_g']),ss['table'])],
        [para('Center of mass X/Y/Z',ss['table']),para(known_com,ss['table']),para(loaded_com,ss['table'])],
        [para('Point-mass inertia diagonal Ixx/Iyy/Izz',ss['table']),para(fmt_diag(known_i)+' g mm^2',ss['table']),para(fmt_diag(loaded_i)+' g mm^2',ss['table'])]]
    story += [table(mr,[124,doc.width*.37,doc.width*.63-124]),
        Spacer(1,2*mm),
        para('Point-mass inertia tensor rows/columns X, Y, Z (g mm^2)',ss['small']),
        table([[para('Case',ss['table_head']),para('Tensor',ss['table_head'])],
            [para('Known mass',ss['table']),para(fmt_tensor(known_i),ss['table'])],
            [para('Separate sensitivity',ss['table']),para(fmt_tensor(loaded_i),ss['table'])]],
            [105,doc.width-105],padd=3),
        para('The known sum contains 485 mass-bearing links. The OpenRB PCB envelope is the sole unknown-mass item and stays unknown in the BOM. The sensitivity adds 10 g controller + 8 g wiring from candidate_r02.json, both lumped at actual board-envelope center ({:.3f}, {:.3f}, {:.3f}) mm. These assumptions do not change the BOM. Neither mass target nor reference envelope is demonstrated; no physical weighing was done.'.format(*screen['controller_board_center_mm']),ss['body']),
        para('Quasi-static demand screen',ss['h2']),
        para('Loads use the separate {:.4f} g sensitivity case, gravity, alpha = 1/3/6, two supports with equal half-weight shares or one-leg full-weight worst case, and horizontal force Fx = 0.30 Fz. Neutral-pose lever arms use actual hip-journal centers and an estimated foot point from the lowest vertices of each native foot solid.'.format(sensitivity['mass_g']),ss['body'])]
    demand=[['Alpha','Support','Fore hip<br/>N m','Hind hip<br/>N m','Pin shear<br/>MPa','Pin bend<br/>MPa','Seat pressure<br/>MPa','B shaft<br/>MPa']]
    for alpha in (1,3,6):
        for support, label in (('two_legs_equal_share','2-leg equal'),('one_leg_worst_case','1-leg worst')):
            fore=next(c for c in cases if c['alpha']==alpha and c['support']==support and c['leg']=='foreL')
            hind=next(c for c in cases if c['alpha']==alpha and c['support']==support and c['leg']=='hindL')
            spine=next(c for c in spine_cases if c['alpha']==alpha and c['support']==support)
            demand.append([str(alpha),label,'{:.4f}'.format(fore['hip_static_moment_Nm']),
                '{:.4f}'.format(hind['hip_static_moment_Nm']),'{:.2f}'.format(fore['pin_single_shear_MPa']),
                '{:.2f}'.format(fore['pin_nominal_bending_stress_MPa']),
                '{:.2f}'.format(fore['PA12_bearing_seat_projected_pressure_MPa']),
                '{:.2f}'.format(spine['nominal_bending_stress_MPa'])])
    demand=[[para(str(c),ss['table_head']) if r==0 else para(str(c),ss['table']) for c in row] for r,row in enumerate(demand)]
    widths=[42,75,54,54,51,53,63,doc.width-392]
    story += [table(demand,widths,row_bgs=[PALE,colors.white,PALE,colors.white,PALE,colors.white]),
        para('Demands only, not material allowables or PASS results. Pin stress uses d=1.9 mm, single-shear area, and a 3.925 mm native bearing-to-joint-plane overhang; bending is a simplified circular beam estimate. Seat pressure uses 4.0 x 1.2 mm projected bearing area. Spine B shaft uses a simply-supported central point load, dia 3.6 mm and assumed 60 mm maximum span. Contact distribution, support reaction sharing, dynamics and local failure modes are not solved.',ss['small']),
        para('At alpha 6, one-leg hip moments are {:.0f}% fore and {:.0f}% hind of the published XC330-M181-T 0.60 N m stall torque at 5 V. Stall is not a continuous-duty limit; no thermal, speed, duty-cycle, impact or fatigue margin is shown. Cable terminal force/friction and all structural allowables remain unknown.'.format(
            100*next(c['hip_moment_fraction_of_XC330_M181_T_stall_at_5V'] for c in cases if c['alpha']==6 and c['support']=='one_leg_worst_case' and c['leg']=='foreL'),
            100*next(c['hip_moment_fraction_of_XC330_M181_T_stall_at_5V'] for c in cases if c['alpha']==6 and c['support']=='one_leg_worst_case' and c['leg']=='hindL')),ss['body']), PageBreak()]

    # Limits and evidence state.
    story += [para('5 | Interfaces, open items and release status',ss['h1']),
        para('Supplier dimensions and physical fits',ss['h2']),
        para('ROBOTIS text confirms the XL/XC nominal motor case envelope and lists drawings, but exact output center, case mounting pattern, horn mating geometry and connector-inclusive bounds were not obtained. OpenRB published board outline is 25 x 66 mm; thickness, mounting holes, populated component dimensions and connectors remain unverified. Do not treat placeholder motor or board solids as complete vendor CAD.',ss['body']),
        para('Nominal candidate stackups requiring metrology: 4.05 mm bearing seat / 4.00 mm OD gives 0.05 mm diametral clearance; 1.90 mm shaft / 2.00 mm bearing bore gives 0.10 mm; controller clamp bore 2.50 mm / fixed tie OD 2.40 mm gives 0.10 mm. The PA12 bearing boss nominal outer dia. 7.00 mm gives a 1.475 mm radial wall. These are geometry assumptions, not tolerance limits.',ss['body']),
        para('Spring parameters are assumptions: extension free length 14 mm and rate 0.25 N/mm; compression free length 18 mm and rate 0.4 N/mm; compression solid length 6 mm plus 1 mm bind margin. Catalogue identity, preload, fatigue, end form and measured lengths are open. Positive cable-capture geometry is modeled; required grip force, surface preparation, clamp torque, friction and slip limit are unverified.',ss['body']),
        para('Verification boundary',ss['h2']),
        para('The current primary-MCP check sampled the C1/C2 moving frame pair against two frame pieces at 361 states and reported PASS with a 0.35 mm minimum gap. This is a scoped pairwise clearance result only. Full whole-robot motion remains unqualified; the check does not establish whole-assembly G3, loaded equilibrium, strength or manufacturing accuracy. The earlier 472-link frame/clamp report is a partial integration only. This manual makes no G3, G4 or G5 pass claim. Fabrication release is not established.',ss['body'])]
    blockers=[
        'Revision-matched motor mounting/output/horn drawings and populated connector clearance.',
        'Measured OpenRB board thickness, component/connector keepouts, mounting strategy and mass.',
        'Bearing, shaft, clip, screw engagement and printed-fit tolerance stackups.',
        'Spring catalogue/rate/free-length/preload and cable terminal holding/slip evidence.',
        'Material/process allowables, safety factors, frame load-path review and full assembly collision/access evidence.',
        'Final drawing/export checks and physical build inspection.'
    ]
    blockerdata=[[para('Open release blocker',ss['table_bold'])]]+[[para('- '+b,ss['table'])] for b in blockers]
    story += [table(blockerdata,[doc.width],header=False),
        para('Evidence files',ss['h2']),
        para('Native candidate: cad/flexor_r07_robot.FCStd. BOM: bom/bom_r07.csv and bom/instances_r07.csv. Mass and envelope: reports/verification/r07_mass_envelope.json. Mass/CoM/inertia/load source: reports/verification/r07_engineering_screen.json. Current scoped 361-state C1/C2-vs-two-frame PASS is reported by the primary MCP review; whole-robot motion is unqualified. Earlier partial report: reports/verification/r07_frame_clamps_neutral.json. Supplier evidence: reports/sources/supplier_interfaces.md and reports/sources/supplier_completion_r07.md. Actual screenshots used here: reports/views/r07_robot_assembled.png, r07_robot_side.png, r07_spine_torso_frames.png, r07_bare_lumbar.png, r07_spine_source_facing.png.',ss['small']),
        para('Primary context: Wang et al., Science Advances 12 (2026), eaed5603, DOI 10.1126/sciadv.aed5603; supplementary Table S1 and source figures are summarized in docs/01_reference_evidence.md and docs/13_candidate_frames_r06.md. ROBOTIS exact product manuals and drawing retrieval outcomes are logged in reports/sources/supplier_completion_r07.md.',ss['small']), PageBreak()]

    # Exact complete BOM appendix; retain CSV quantity and IDs.
    story += [para('Appendix A | Complete r07 BOM index',ss['h1']),
        para('All 105 unique part numbers and aggregate quantities below are generated directly from bom/bom_r07.csv. Line-item IDs/revisions/roles/mass/provenance in the CSV remain authoritative. A provisional geometry label is not supplier approval.',ss['body'])]
    bomdata=[[para('Assembly group',ss['table_head']),para('Exact part number',ss['table_head']),para('Qty',ss['table_head'])]]
    for group,pn,qty in bom:
        bomdata.append([para(group,ss['small']),para(pn,ss['small']),para(str(qty),ss['table'])])
    widths=[112,doc.width-150,38]
    story.append(LongTable(bomdata,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=1,style=TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),NAVY),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('GRID',(0,0),(-1,-1),.3,GRID),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('ALIGN',(2,0),(2,-1),'RIGHT')])) )
    story += [Spacer(1,5*mm), para('Appendix totals: %d unique part numbers, %d assembly instances. Controller PCB mass remains unknown; the separate 10 g controller + 8 g harness sensitivity case is not booked as a purchase mass.' % (
        len(bom), sum(x[2] for x in bom)), ss['body'])]

    doc.build(story)
    return {'pdf':str(OUT),'bom_unique_pns':len(bom),'bom_instances':sum(x[2] for x in bom)}


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
