#!/usr/bin/env python3
"""Structural qualification tests; optional integration uses the actual pinned cache."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import numpy as np

from qualify_ope_archives import (MANIFEST, checked_file, name_mapping, qualify,
                                  read_array, registrations, summarize)


class StructuralTests(unittest.TestCase):
    def test_repeated_terminal_is_not_a_recording_reset(self):
        got = summarize(np.array([0, 1, 2, 0]), np.array(['a', 'a', 'a', 'b']),
                        np.array([False, True, True, False]),
                        np.array([False, False, True, True]), np.zeros(4), 0)
        self.assertEqual(got['segments'], 2)
        self.assertEqual(got['done_or_truncated_rows'], 3)
        self.assertEqual(got['flags_before_segment_end'], 1)
        self.assertEqual(got['segments_per_policy'], {'a': 1, 'b': 1})

    def test_one_based_start_and_final_singleton(self):
        got = summarize(np.array([1, 2, 1]), np.array(['a']*3), np.zeros(3, bool),
                        np.array([False, True, True]), np.zeros((3, 1, 2)), 1)
        self.assertEqual(got['length_distribution'], {1: 1, 2: 1})
        self.assertEqual(got['unflagged_segment_ends'], 0)

    def test_bad_progression_or_policy_change_rejected(self):
        for t, names in [([0, 2], ['a', 'a']), ([0, 1], ['a', 'b'])]:
            with self.subTest(t=t, names=names), self.assertRaises(ValueError):
                summarize(np.array(t), np.array(names), np.zeros(2, bool),
                          np.ones(2, bool), np.zeros(2), 0)

    def test_hash_mismatch_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, 'a.zip').write_bytes(b'wrong archive')
            with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
                checked_file(d, 'a.zip', {'sha256': '0'*64})

    def test_only_exact_policy_names_map(self):
        self.assertEqual(name_mapping(['p_0.5', 'p_0.5_1'], {'p_0.5': 'config.json'}),
                         {'p_0.5': 'config.json', 'p_0.5_1': None})

    def test_registrations_are_parsed_without_execution(self):
        source = "raise RuntimeError('must not run')\nregister(id='real', entry_point='x', kwargs={'dataset_url':'https://host/sim.zip'})"
        self.assertEqual(registrations(source)['real']['archive'], 'sim.zip')

    def test_outcome_array_is_rejected_before_read(self):
        with self.assertRaisesRegex(ValueError, 'Outside structural scope'):
            read_array(None, '', 'rewards')

    def test_partial_chunk_and_missing_chunk(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d, 'structural.zip')
            meta = {'zarr_format': 2, 'order': 'C', 'filters': None,
                    'compressor': None, 'shape': [3], 'chunks': [2], 'dtype': '<i8'}
            with zipfile.ZipFile(f, 'w') as z:
                z.writestr('timestep/.zarray', json.dumps(meta))
                z.writestr('timestep/0', np.array([0, 1], dtype='<i8').tobytes())
            with zipfile.ZipFile(f) as z, self.assertRaises(KeyError):
                read_array(z, '', 'timestep')
            with zipfile.ZipFile(f, 'a') as z:
                z.writestr('timestep/1', np.array([2, 0], dtype='<i8').tobytes())
            with zipfile.ZipFile(f) as z:
                np.testing.assert_array_equal(read_array(z, '', 'timestep'), [0, 1, 2])


@unittest.skipUnless(os.environ.get('RACING_OPE_CACHE'), 'actual archive cache not supplied')
class ActualArchiveTests(unittest.TestCase):
    def test_actual_mapping_counts_and_outcome_read_boundary(self):
        # Every ZIP member actually opened must be a declared structural array.
        original = zipfile.ZipFile.read
        def read_structural(z, member, *args, **kwargs):
            name = member.filename if isinstance(member, zipfile.ZipInfo) else member
            self.assertIn(name.split('/')[-2], {'timestep', 'model_name', 'done', 'truncated', 'log_prob'})
            return original(z, member, *args, **kwargs)
        with patch.object(zipfile.ZipFile, 'read', read_structural):
            result = qualify(Path(os.environ['RACING_OPE_CACHE']), json.loads(MANIFEST.read_text()))
        committed = json.loads((MANIFEST.parent / 'result.json').read_text())
        self.assertEqual(json.loads(json.dumps(result)), committed)
        real = result['archives']['f110-real-stoch-v2.zip']['segments_per_policy']
        reg = result['registrations']['f110-real-stoch-v2']
        self.assertTrue(set(reg['eval_model_names']).issubset(real))
        self.assertEqual(set(reg['eval_model_names']), set(reg['eval_names_missing_from_loaded_archive']))
        v1 = result['archives']['f110-real-v1.zip']
        self.assertTrue(v1['other_structural_roots_equal'][''])
        self.assertGreater(v1['done_or_truncated_rows'], v1['segments'])
        self.assertTrue(all(result['archives']['f110-real-stoch-v2.zip']['benchmark_config_mapping'].values()))


if __name__ == '__main__':
    unittest.main()
