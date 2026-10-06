#!/usr/bin/env python3
"""Inspect only pinned structural arrays. Never call the upstream dataset loader."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import zipfile

import numpy as np
import numcodecs

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'runs/ope_qualification/inputs.json'
ALLOWED = frozenset(('timestep', 'model_name', 'done', 'truncated', 'log_prob'))


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def checked_file(cache, name, spec):
    path = Path(cache) / name
    actual = (hashlib.sha256(json.dumps(json.loads(path.read_text()), sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
              if 'canonical_json_sha256' in spec else sha256(path))
    if actual != spec.get('canonical_json_sha256', spec.get('sha256')):
        raise ValueError(f'Hash mismatch: {name}')
    return path


def read_array(archive, prefix, key):
    """Read the Zarr-v2 structural layout actually present in these archives.

    No pickle or upstream code execution. Missing chunks are errors rather than
    implicit zeros, since zeros can create false resets or policy mappings.
    """
    if key not in ALLOWED:
        raise ValueError(f'Outside structural scope: {key}')
    stem = prefix + key + '/'
    meta = json.loads(archive.read(stem + '.zarray'))
    if meta['zarr_format'] != 2 or meta['order'] != 'C':
        raise ValueError('Unsupported structural array layout')
    filters = meta.get('filters') or []
    if filters not in ([], [{'id': 'vlen-utf8'}]):
        raise ValueError('Unsupported structural codec')
    if meta['dtype'] == '|O' and filters != [{'id': 'vlen-utf8'}]:
        raise ValueError('Object data must use UTF-8, never pickle')
    shape, chunks = meta['shape'], meta['chunks']
    out = np.empty(shape, dtype=meta['dtype'])
    grid = (range((n + c - 1) // c) for n, c in zip(shape, chunks))
    for index in itertools.product(*grid):
        payload = archive.read(stem + '.'.join(map(str, index)))
        if meta['compressor']:
            payload = numcodecs.get_codec(meta['compressor']).decode(payload)
        for codec in reversed(filters):
            payload = numcodecs.get_codec(codec).decode(payload)
        decoded = (np.asarray(payload, dtype=meta['dtype']) if filters else
                   np.frombuffer(payload, dtype=meta['dtype']))
        decoded = decoded.reshape(chunks)
        target = tuple(slice(i*c, min((i+1)*c, n)) for i, c, n in zip(index, chunks, shape))
        out[target] = decoded[tuple(slice(0, s.stop-s.start) for s in target)]
    return out


def summarize(t, names, done, truncated, logs, start_value):
    if any(a.shape != t.shape for a in (names, done, truncated)) or t.ndim != 1:
        raise ValueError('Structural row alignment differs')
    if logs.shape[0] != len(t) or not len(t):
        raise ValueError('Missing or misaligned log-probability records')
    starts = np.r_[0, np.flatnonzero(t[1:] <= t[:-1]) + 1]
    ends = np.r_[starts[1:], len(t)]
    # A second rule uses the declared start marker, independently of differences.
    marker_starts = np.flatnonzero(t == start_value)
    if not np.array_equal(starts, marker_starts):
        raise ValueError('Reset and start-marker segmentations disagree')
    if not all(np.array_equal(t[s:e], np.arange(start_value, start_value+e-s))
               for s, e in zip(starts, ends)):
        raise ValueError('Non-unit timestep progression within a segment')
    if not all(np.all(names[s:e] == names[s]) for s, e in zip(starts, ends)):
        raise ValueError('Policy changes within a recording segment')
    terminal = done | truncated
    end_mask = np.zeros(len(t), dtype=bool)
    end_mask[ends-1] = True
    lengths = ends - starts
    policies = Counter(str(n) for n in names[starts])
    return {
        'rows': len(t), 'segments': len(starts), 'policy_names': len(policies),
        'length_distribution': dict(sorted(Counter(map(int, lengths)).items())),
        'length_range_rows': [int(lengths.min()), int(lengths.max())],
        'start_marker_count': len(marker_starts), 'start_timestep': start_value,
        'unit_steps_within_segments': True, 'policy_constant_within_segments': True,
        'done_rows': int(done.sum()), 'truncated_rows': int(truncated.sum()),
        'done_or_truncated_rows': int(terminal.sum()),
        'unflagged_segment_ends': int((~terminal[end_mask]).sum()),
        'flags_before_segment_end': int(terminal[~end_mask].sum()),
        'both_flags_rows': int((done & truncated).sum()),
        'segments_per_policy': dict(sorted(policies.items())),
        'log_prob_shape': list(logs.shape),
        'log_prob_all_finite': bool(np.isfinite(logs).all()),
        'log_prob_all_zero': bool(np.all(logs == 0)),
    }


def registrations(source):
    """Literal AST inspection, without importing gym or running the loader."""
    result = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'register':
            args = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords}
            spec = args['kwargs']
            result[args['id']] = {
                'archive': spec['dataset_url'].rsplit('/', 1)[-1],
                'eval_model_names': spec.get('eval_model_names', []),
                'bad_agents': spec.get('bad_agents', []),
                'bad_trajectory_indices': spec.get('bad_trajectories', []),
            }
    return result


def config_paths(tree):
    return {Path(e['path']).stem: e['path'] for e in tree['tree']
            if e['type'] == 'blob' and '/agent_configs/' in '/' + e['path']
            and e['path'].endswith('.json')}


def name_mapping(names, configs):
    # Exact names only. A shared prefix or near-match cannot identify a policy.
    return {n: configs.get(n) for n in sorted(names)}


def qualify(cache, manifest):
    files = {n: checked_file(cache, n, s) for n, s in manifest['sources'].items()}
    trees = {n: json.loads(files[n].read_text()) for n in files if n.endswith('_tree.json')}
    for tree in trees.values():
        if tree['truncated']:
            raise ValueError('Incomplete source tree')
    configs = config_paths(trees['benchmark_policy_tree.json'])
    bundled = config_paths(trees['f1tenth_orl_dataset_tree.json'])
    archives = {}
    for name, spec in manifest['archives'].items():
        path = checked_file(cache, name, spec)
        with zipfile.ZipFile(path) as z:
            arrays = {k: read_array(z, spec['prefix'], k) for k in sorted(ALLOWED)}
            roots = sorted(n[:-len('timestep/.zarray')] for n in z.namelist()
                           if n.endswith('timestep/.zarray'))
            duplicate_equal = {}
            for prefix in roots:
                if prefix != spec['prefix']:
                    duplicate_equal[prefix] = all(np.array_equal(arrays[k], read_array(z, prefix, k))
                                                  for k in sorted(ALLOWED))
            info = summarize(arrays['timestep'], arrays['model_name'], arrays['done'],
                             arrays['truncated'], arrays['log_prob'], spec['start_timestep'])
        info.update({'archive_sha256_verified': True, 'prefix': spec['prefix'],
                     'other_structural_roots_equal': duplicate_equal,
                     'benchmark_config_mapping': name_mapping(info['segments_per_policy'], configs),
                     'bundled_config_mapping': name_mapping(info['segments_per_policy'], bundled)})
        archives[name] = info
    regs = registrations(files['__init__.py'].read_text())
    for spec in regs.values():
        actual = archives[spec['archive']]
        spec['eval_names_missing_from_loaded_archive'] = sorted(
            set(spec['eval_model_names']) - actual['segments_per_policy'].keys())
        spec['bad_indices_outside_loaded_rows'] = [i for i in spec['bad_trajectory_indices']
                                                   if i < 0 or i >= actual['rows']]
    real = set(archives['f110-real-v1.zip']['segments_per_policy'])
    sim = set(archives['f110-sim-v1.zip']['segments_per_policy'])
    return {
        'scope': manifest['scope'],
        'inputs_sha256': sha256(MANIFEST),
        'script_sha256': sha256(__file__),
        'arrays_decoded': sorted(ALLOWED), 'archives': archives, 'registrations': regs,
        'v1_name_correspondence': {'exact_common': sorted(real & sim),
                                   'real_only': sorted(real - sim), 'sim_only': sorted(sim - real)},
        'license_filename_candidates': {n: [e['path'] for e in t['tree']
            if any(s in Path(e['path']).name.lower() for s in ('license', 'licence', 'copying'))]
            for n, t in trees.items()},
        'gates': {
            'data_and_code_reuse_rights': 'unknown; no explicit grant established',
            'episode_meaning_and_independence': 'unqualified; structural segments only',
            'policy_executability': 'unqualified; filename matches only, no actor executed',
            'fqe': 'blocked pending rights, mapped target actions, observation reconstruction, horizon and coverage',
            'is_wis_ratio_dr': 'blocked; additionally need joint executed-action densities and support',
            'finite_horizon_reference': 'not executed; permission and episode/policy semantics unresolved',
            'return_or_rank_analysis': 'not executed',
        },
    }


def render_table(result, output):
    rows = ['# Raw archive structure', '',
            'Generated by `experiments/qualify_ope_archives.py` from `result.json`.',
            'Counts describe unfiltered recording segments and exact policy-name strings.', '',
            '| Archive | Rows | Segments | Policy names | Rows/segment | Flags before segment end |',
            '| --- | ---: | ---: | ---: | --- | ---: |']
    for name, info in result['archives'].items():
        lo, hi = info['length_range_rows']
        rows.append(f"| {name} | {info['rows']:,} | {info['segments']:,} | {info['policy_names']} | {lo} to {hi} | {info['flags_before_segment_end']:,} |")
    output.write_text('\n'.join(rows) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = qualify(args.cache, json.loads(MANIFEST.read_text()))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'result.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    render_table(result, args.output / 'structure.md')
    print(json.dumps({'archives': len(result['archives']), 'gates': result['gates']}, indent=2))


if __name__ == '__main__':
    main()
