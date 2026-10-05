"""Census published bag metadata before assigning a session-separated split.

This task stops at missing session provenance. No bag is downloaded or parsed.
Distinct bag hashes cannot establish disjoint acquisition sessions or segments.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def qualify(metadata_path, output):
    registration_path = ROOT / 'runs/driving_split_qualification/registration.json'
    registration = json.loads(registration_path.read_text())
    content = metadata_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != registration['metadata']['sha256']:
        raise ValueError('Metadata differs from the registered snapshot')
    record = json.loads(content)
    previous = json.loads((ROOT / 'runs/real_command_response/source.json').read_text())
    exposed = previous['development_bag']['name']
    rows = []
    checksums = defaultdict(list)
    pattern = re.compile(r'ex-(.+)-r(\d+)_(\d{4}-\d{2}-\d{2})-(\d{2}-\d{2}-\d{2})\.bag')
    for item in sorted(record['files'], key=lambda entry: entry['key']):
        if not item['key'].endswith('.bag'):
            continue
        match = pattern.fullmatch(item['key'])
        if match is None:
            raise ValueError('Unrecognized bag filename: '+item['key'])
        series, repetition, date, clock = match.groups()
        checksums[item['checksum']].append(item['key'])
        rows.append({
            'file': item['key'], 'url': item['links']['self'],
            'bytes': item['size'], 'published_checksum': item['checksum'],
            'sha256': previous['development_bag']['sha256'] if item['key'] == exposed else None,
            'filename_series': series, 'filename_repetition': repetition,
            'filename_start': date+'T'+clock.replace('-', ':'),
            'timezone': 'not supplied', 'acquisition_session_id': None,
            'segment_parent_id': None, 'recorded_end_time': None,
            'role': 'development_exposed' if item['key'] == exposed else 'unassigned_unopened',
            'role_group': 'unresolved_acquisition_group',
        })
    if not any(row['file'] == exposed for row in rows):
        raise ValueError('Previously exposed development bag missing from metadata')
    # The source review in registration supplies the interpretation. This census
    # does not infer a session ID from a date, series name or distinct checksum.
    result = {
        'status': 'blocked_before_split_assignment',
        'executed_utc': datetime.now(timezone.utc).isoformat(),
        'registration_sha256': hashlib.sha256(registration_path.read_bytes()).hexdigest(),
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'metadata_sha256': digest,
        'record_id': record['id'], 'record_updated': record['updated'],
        'data_license': record['metadata']['license'],
        'bag_count': len(rows),
        'filename_dates': sorted({row['filename_start'].split('T')[0] for row in rows}),
        'exact_duplicate_checksum_groups': [names for names in checksums.values() if len(names) > 1],
        'distinct_published_checksums': len(checksums),
        'qualified_separate_final_groups': 0,
        'additional_bags_acquired': 0, 'additional_bags_parsed': 0,
        'training_runs_fitted': 0, 'final_runs_scored': 0,
        'longitudinal_status': 'not executed: split prerequisite unresolved',
        'lateral_status': 'not executed: split prerequisite unresolved; no lateral qualification or coefficients inferred',
        'files': rows,
        'finding': 'Published metadata identifies separate continuous bag runs but does not map acquisition sessions or parent segments. Filename dates and distinct hashes do not resolve that missing provenance.',
        'grouping': 'Keep the unresolved group together until source-backed session membership is available. This is a conservative hold, not a finding that all files share one session.',
        'required_evidence': 'A source-backed file-to-session and segment mapping establishing disjoint acquisition units, including any shared vehicle/surface/configuration. Then register roles before accessing unopened outcomes.',
    }
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('status', 'bag_count', 'filename_dates', 'distinct_published_checksums', 'qualified_separate_final_groups', 'final_runs_scored')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    qualify(args.metadata, args.output)
