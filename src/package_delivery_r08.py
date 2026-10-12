"""Fail-closed inventory of accepted frozen r08 deliverables; never mutates CAD.

Prepare first; call run() only after the lead authorizes final validation.
PDF/final-review evidence contracts are documented in the preparation review.
"""
from __future__ import annotations
import hashlib
import json
import math
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_NATIVE_SHA256 = '3832778436b75539d0ecf0e95df935099005331157c1328c2f77389985a817c8'
PACKAGE_STATUS = 'EXPORTS_AND_STEP_ROUNDTRIP_VALIDATED_NO_FABRICATION_RELEASE'
OUTPUT = 'reports/delivery_manifest_r08.json'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def path(value):
    p = Path(value)
    p = (ROOT / p).resolve() if not p.is_absolute() else p.resolve()
    require(p.is_relative_to(ROOT.resolve()), 'Artifact outside project: ' + str(p))
    require(p.is_file() and p.stat().st_size > 0, 'Missing/empty artifact: ' + str(p))
    return p


def digest(value):
    h = hashlib.sha256()
    with path(value).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(value):
    return json.loads(path(value).read_text(encoding='utf-8'))


def native_match(record, label):
    values = [record[k] for k in ('native_sha256', 'canonical_robot_sha256', 'source_sha256') if k in record]
    require(values and all(v == FROZEN_NATIVE_SHA256 for v in values), label + ': missing/stale frozen native SHA')


def page_count(value):
    p = path(value)
    try:
        from pypdf import PdfReader
    except ImportError:
        result = subprocess.run(['pdfinfo', str(p)], capture_output=True, text=True, check=True)
        counts = [int(line.split(':', 1)[1]) for line in result.stdout.splitlines() if line.startswith('Pages:')]
        require(len(counts) == 1, 'Cannot determine PDF pages: ' + str(p))
        return counts[0]
    return len(PdfReader(str(p)).pages)


def run():
    """Validate all final gates, write inventory, and return its absolute Path.

    Writes only delivery_manifest_r08.json on success. A failure removes an
    existing delivery manifest so a stale success cannot represent this run.
    """
    target = ROOT / OUTPUT
    target.unlink(missing_ok=True)
    files = set()

    def add(value, expected_sha=None):
        p = path(value)
        require(p != target.resolve(), 'Delivery manifest cannot inventory itself')
        if expected_sha is not None:
            require(digest(p) == expected_sha, 'Artifact digest mismatch: ' + str(p))
        files.add(p)
        return p

    def evidence(value):
        add(value)
        return read(value)

    native = add('cad/flexor_r08_robot.FCStd', FROZEN_NATIVE_SHA256)
    check = evidence('reports/verification/r08_native_checks.json')
    native_match(check, 'Native check')
    require(check.get('status') == 'PASS' and check.get('file_unchanged') is True and
            check.get('reopened_recomputed') is True, 'Native reopen/recompute gate incomplete')
    require(check.get('physical_instances') == 486 and check.get('editable_bodies') == 95, 'Native counts mismatch')

    freeze = evidence('reports/verification/r08_motion_partitions/freeze.json')
    native_match(freeze, 'Motion freeze')
    for key, value in freeze.get('dependency_sha256', {}).items():
        add('src/' + key, value)
    add('parameters/assembly_r08.json', freeze['config_sha256'])
    for stage, count, summary_name in (
            ('full', 985, 'full_summary.json'), ('cage_spine', 361, 'cage_spine_361.json')):
        prefix = 'reports/verification/r08_motion_partitions/'
        summary = evidence(prefix + summary_name)
        require(summary.get('status') == 'PASS', stage + ' motion not PASS')
        require(summary.get('records_found', summary.get('samples_completed')) == count, stage + ' motion count mismatch')
        require(summary.get('samples_expected') == count, stage + ' expected count mismatch')
        require(summary.get('hash_coherence') and all(summary['hash_coherence'].values()), stage + ' hash coherence failed')
        for key in ('missing_sample_ids', 'extra_sample_ids', 'duplicate_sample_ids', 'failed_records', 'overlaps', 'errors', 'baseline_overlaps'):
            require(not summary.get(key), stage + ' contains incomplete/failed records: ' + key)
        if 'native_sha256' in summary:
            native_match(summary, stage + ' summary')
        statuses = summary.get('partition_statuses', {})
        require(statuses and all(v == 'PASS' for v in statuses.values()), stage + ' partitions incomplete')
        completed = 0
        for index in statuses:
            partition = evidence(prefix + stage + '_part_' + str(index) + '.json')
            native_match(partition, stage + ' partition ' + str(index))
            require(partition.get('status') == 'PASS', stage + ' partition not PASS')
            require(partition.get('records') and all(r.get('status') == 'PASS' for r in partition['records']),
                    stage + ' partition record incomplete')
            completed += len(partition['records'])
            require(partition.get('native_file_unchanged') is True and partition.get('document_unchanged') is True,
                    stage + ' partition mutation gate failed')
            require(partition.get('config_sha256') == freeze['config_sha256'] and
                    partition.get('freeze_sha256') == digest(prefix + 'freeze.json'), stage + ' partition freeze stale')
        require(completed == count, stage + ' actual partition record count mismatch')
        if stage == 'full':
            plan = evidence(prefix + 'full_manifest.json')
            require(summary.get('manifest') == plan and plan.get('count') == count, 'Full motion plan/summary mismatch')

    exports = evidence('reports/package_manifest_r08.json')
    require(exports.get('revision') == 'r08' and exports.get('status') == PACKAGE_STATUS, 'Exports not accepted')
    require(exports['native_document']['sha256'] == FROZEN_NATIVE_SHA256 and exports.get('native_file_unchanged') is True,
            'Export source stale')
    require(exports.get('physical_link_count') == 486, 'Export instance count mismatch')
    for record in [exports['assembly_step']] + exports['bom_and_mass_files']:
        add(record['path'], record['sha256'])
    for part in exports['parts']:
        for value in part['files']:
            require(value.startswith(('exports/step/r08/', 'exports/print/r08/')), 'Export path outside accepted r08 scope')
            add(value, part['sha256'][value])
    add('exports/step/r08/README_volume_validation.md')

    drawings = evidence('drawings/r08/drawing_manifest_r08.json')
    native_match(drawings, 'Drawings')
    require(drawings.get('revision') == 'r08' and drawings.get('status') == 'PASS_NATIVE_DIMENSIONS' and
            drawings.get('visual_review') == 'PASS' and drawings.get('pdf_exports') == 'COMPLETE' and not drawings.get('errors'),
            'Drawing acceptance incomplete')
    sheets = drawings['sheets']
    dimensions = sum(len(s['dimensions']) for s in sheets)
    require(sheets and dimensions > 0 and drawings['sheet_count'] == len(sheets) and
            drawings['dimension_count'] == dimensions, 'Drawing actual counts disagree')
    require(len({s['sheet'] for s in sheets}) == len(sheets), 'Duplicate drawing sheets')
    companion = add('cad/flexor_r08_drawings.FCStd', drawings['native_companion_sha256'])
    add('drawings/templates/A4_candidate.svg')
    editable_template = add('drawings/r08/templates/A4_r08_editable.svg')
    with zipfile.ZipFile(companion) as archive:
        document_xml = ET.fromstring(archive.read('Document.xml'))
    template_files = [node.find('String').get('value') for node in document_xml.findall('.//Property')
                      if node.get('name') == 'Template' and node.get('type') == 'App::PropertyFile'
                      and node.find('String') is not None]
    require(len(template_files) == len(sheets), 'Companion template/sheet count mismatch')
    for value in template_files:
        require(path(value) == editable_template, 'Companion template does not resolve to repository r08 template')
    for sheet in sheets:
        require(not sheet.get('errors') and sheet.get('export_layout_status') == 'EXPORTED_CURRENT_NATIVE_LAYOUT', 'Drawing sheet incomplete')
        require(set(sheet.get('export_sha256', {})) >= {'svg', 'pdf'}, 'Drawing sheet export hashes missing')
        for kind in ('svg', 'pdf'):
            p = add(sheet['exports'][kind], sheet['export_sha256'][kind])
            require(p.is_relative_to((ROOT/'drawings/r08').resolve()), 'Drawing outside r08 directory')

    profiles = evidence('exports/profiles/r08/profile_manifest_r08.json')
    native_match(profiles, 'Profiles')
    require(profiles.get('revision') == 'r08' and profiles.get('status') == 'PASS_EXACT_PROFILE_READBACK' and
            profiles.get('source_file_unchanged') is True and not profiles.get('errors'), 'Profiles not accepted')
    require(profiles.get('profile_count') == len(profiles['profiles']) and profiles['profiles'], 'Profile count mismatch')
    for profile in profiles['profiles']:
        require(profile['readback']['status'] == 'PASS', 'Profile readback failed')
        add(profile['path'], profile['sha256'])
    reproduction = evidence('reports/verification/r08_source_reproduction.json')
    native_match(reproduction, 'Source reproduction')
    require(reproduction.get('status') == 'PASS', 'Source reproduction failed')

    capture = evidence('reports/views/r08_capture_manifest.json')
    native_match(capture, 'Image capture review')
    require(capture.get('revision') == 'r08' and capture.get('status') == 'PASS_CAPTURED_RESTORED' and
            capture.get('visual_review') == 'PASS', 'Image capture visual review incomplete')
    require(capture.get('captures'), 'No reviewed image captures')
    for record in capture['captures']:
        add(record['path'], record['sha256'])
    fidelity = evidence('reports/reviews/r08_source_fidelity.json')
    require(fidelity.get('revision') == 'r08' and
            str(fidelity.get('disposition', '')).startswith('PRINCIPAL_R07_FACE_OWNERSHIP_ERROR_CORRECTED;') and
            not fidelity.get('required_morphology_corrections'), 'Principal source-fidelity correction not accepted')
    fidelity_hashes = fidelity.get('artifacts_sha256', {})
    required_fidelity = {'cad/flexor_r08_robot.FCStd', 'src/spine_frame_r08.py',
                         'parameters/assembly_r08.json'}
    require(required_fidelity <= set(fidelity_hashes), 'Source-fidelity native/source/parameter evidence incomplete')
    require(any(k.startswith('reports/views/r08_') for k in fidelity_hashes), 'Source-fidelity image evidence missing')
    require(fidelity_hashes['cad/flexor_r08_robot.FCStd'] == FROZEN_NATIVE_SHA256, 'Source-fidelity native SHA stale')
    for value, sha in fidelity_hashes.items():
        add(value, sha)
    for value in fidelity.get('source_evidence', []):
        candidate = Path(value)
        candidate = (ROOT / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        # External clipboard files remain recorded provenance in fidelity JSON;
        # only existing repository source images are delivery artifacts.
        if candidate.is_relative_to(ROOT.resolve()) and candidate.is_file():
            add(candidate)

    motion_images = evidence('reports/motion/r08/capture_manifest.json')
    native_match(motion_images, 'Motion capture')
    require(motion_images.get('status') == 'PASS_CAPTURED_RESTORED' and motion_images.get('native_file_unchanged') is True,
            'Motion capture incomplete')
    require(len(motion_images.get('frames', [])) == 24, 'Actual CAD motion capture requires 24 frames')
    require([r.get('frame') for r in motion_images['frames']] == list(range(24)) and
            [r.get('spine_phase_deg') for r in motion_images['frames']] == list(range(0, 360, 15)),
            'Actual CAD frame sequence/phase mismatch')
    for record in motion_images['frames']:
        add(record['path'], record['sha256'])

    animation = motion_images.get('animation', {})
    require(animation.get('actual_cad_capture') is True and animation.get('frames') == 24 and
            animation.get('format') == 'GIF', 'Actual CAD animation evidence incomplete')
    animation_path = add(animation['path'], animation['sha256'])
    require(animation_path.is_relative_to((ROOT / 'reports/motion/r08').resolve()), 'Animation outside accepted r08 output')
    from PIL import Image
    with Image.open(animation_path) as image:
        require(image.format == 'GIF' and image.n_frames == 24, 'Actual GIF does not contain 24 CAD frames')
    contact_sheet = add('reports/motion/r08/contact_sheet.png')
    with Image.open(contact_sheet) as image:
        require(image.format == 'PNG' and image.width > 0 and image.height > 0, 'Invalid motion contact sheet')

    mass = evidence('reports/verification/r08_mass_envelope.json')
    engineering = evidence('reports/verification/r08_engineering_screen.json')
    require(mass.get('revision') == 'r08' and mass.get('status') == 'COMPUTED_FROM_DOCUMENT' and
            mass.get('instance_count') == 486 and mass.get('part_number_count') == 105, 'Mass/BOM counts or calculation incomplete')
    require(engineering.get('native_document') == str(native) and engineering.get('physical_link_count') == 486,
            'Engineering screen source/count mismatch')
    for record, name in ((mass, 'Mass'), (engineering, 'Engineering')):
        if 'native_sha256' in record:
            native_match(record, name)
    require(math.isclose(mass['known_mass_sum_g'], engineering['known_mass']['mass_g'], rel_tol=1e-10), 'Mass reports disagree')
    require(mass['unknown_mass_instance_count'] == len(mass['unknown_mass_instances']), 'Unknown mass count mismatch')
    for name in ('neutral', 'actuators', 'native_edit_restore', 'native_geometry_report'):
        record = evidence('reports/verification/r08_' + name + '.json')
        if 'native_sha256' in record:
            native_match(record, name)
        require(str(record.get('status', '')).startswith('PASS'), name + ' verification incomplete')

    pdf_review = evidence('reports/reviews/r08_pdf_visual_review.json')
    native_match(pdf_review, 'PDF visual review')
    require(pdf_review.get('status') == 'PASS', 'PDF visual review incomplete')
    reviewed_pdfs = {r['path']: r for r in pdf_review['documents']}
    pdf_counts = {}
    for value in ('docs/flexor_r08_assembly_calibration.pdf', 'drawings/flexor_r08_drawing_book.pdf'):
        require(value in reviewed_pdfs, 'Missing final PDF visual review: ' + value)
        record = reviewed_pdfs[value]
        p = add(value, record['sha256'])
        pages = page_count(p)
        require(record.get('visual_review') == 'PASS' and record.get('page_count') == pages and pages > 0,
                'PDF hash/page/visual acceptance mismatch: ' + value)
        pdf_counts[value] = pages
    require(pdf_counts['drawings/flexor_r08_drawing_book.pdf'] == len(sheets), 'Drawing book page count mismatch')

    # Reproducible source may intentionally include historical dependency module
    # names. Old generated CAD/report/export assets are never globbed in.
    for pattern in ('src/*.py', 'src/*.cpp', 'tests/*.py', 'macros/*.FCMacro', 'parameters/*.json', 'docs/*.md'):
        for p in ROOT.glob(pattern):
            add(p)
    for value in ('README.md', 'AGENTS.md', '.gitattributes', 'macros/Rebuild_r08.FCMacro'):
        add(value)
    for value in ('reports/reviews/stl_retainer_repair_r08.md',
                  'reports/reviews/r08_delivery_validator_preparation.md'):
        add(value)

    review_path = path('reports/reviews/r08_final_review.json')
    review = read(review_path)
    native_match(review, 'Final independent review')
    require(review.get('status') == 'PASS_CANDIDATE_WITH_RELEASE_BLOCKERS' and
            review.get('independent_review') is True, 'Final independent review incomplete')
    reviewed = {path(r['path']): r['sha256'] for r in review['reviewed_files']}
    critical_names = (
        'cad/flexor_r08_robot.FCStd', 'cad/flexor_r08_drawings.FCStd',
        'drawings/flexor_r08_drawing_book.pdf', 'docs/flexor_r08_assembly_calibration.pdf',
        'reports/package_manifest_r08.json',
        'reports/verification/r08_motion_partitions/full_summary.json',
        'reports/verification/r08_motion_partitions/cage_spine_361.json',
        'exports/profiles/r08/profile_manifest_r08.json',
        'reports/verification/r08_source_reproduction.json',
        'reports/verification/r08_native_checks.json',
        'bom/bom_r08.csv', 'bom/instances_r08.csv',
        'reports/verification/r08_mass_envelope.json',
        'reports/verification/r08_engineering_screen.json',
        'reports/views/r08_capture_manifest.json',
        'reports/reviews/r08_source_fidelity.json',
        'reports/motion/r08/capture_manifest.json',
        'reports/reviews/r08_pdf_visual_review.json',
        'drawings/r08/drawing_manifest_r08.json')
    critical = {path(value) for value in critical_names}
    require(critical <= set(reviewed), 'Final independent review does not cover complete critical package')
    for p in critical:
        require(reviewed[p] == digest(p), 'Artifact changed after final independent review: ' + str(p))
    add(review_path)
    records = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(files)]
    output = {'status': 'CAD_PACKAGE_VERIFIED', 'revision': 'r08', 'native_sha256': FROZEN_NATIVE_SHA256,
              'physical_instances': 486, 'native_custom_bodies': 95, 'bom_part_numbers': 105,
              'drawing_sheets': len(sheets), 'native_dimensions': dimensions,
              'full_motion_samples': 985, 'cage_spine_samples': 361, 'pdf_page_counts': pdf_counts,
              'mass_summary': {k: mass[k] for k in ('known_mass_sum_g', 'known_purchased_mass_g',
                  'all_geometry_mass_estimate_g', 'unknown_mass_instance_count', 'unknown_mass_instances',
                  'actual_assembled_bbox_mm', 'reference_envelope_mm', 'actual_minus_reference_mm', 'mass_limitations')},
              'engineering_summary': {k: engineering[k] for k in ('known_mass', 'assumed_loaded_sensitivity', 'separate_assumptions', 'limitations')},
              'scope': 'Reviewable editable CAD candidate; exact finite sample coverage only',
              'fabrication_release': 'BLOCKED', 'physical_validation': 'NOT_RUN', 'continuous_clearance': 'NOT_RUN',
              'file_count': len(records), 'files': records,
              'inventory_limit': 'Only accepted r08 generated artifacts and reproducible source/tests/docs/parameters; no failed diagnostic, transient, historical generated asset or self hash.'}
    target.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return target


if __name__ == '__main__':
    print(run())
