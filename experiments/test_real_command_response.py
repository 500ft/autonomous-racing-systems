"""Numerical checks for the transformations actually used on the public bag."""
import unittest
import numpy as np
from real_command_response import fit_response, hold, timing, world_to_tracking


class CommandResponseTests(unittest.TestCase):
    def test_quarter_turn_world_to_tracking_and_quaternion_sign(self):
        q = np.array([0, 0, np.sqrt(.5), np.sqrt(.5)])
        for orientation in (q, -q, 2*q):
            np.testing.assert_allclose(world_to_tracking(orientation, [0, 3, 2]), [3, 0, 2], atol=1e-14)
        with self.assertRaises(ValueError):
            world_to_tracking([0, 0, 0, 0], [1, 2, 3])

    def test_hold_rejects_future_stale_and_end_extrapolation(self):
        x, valid = hold(np.array([1., 2., 4.]), np.array([10., 20., 40.]),
                        np.array([.9, 1., 1.4, 1.8, 2., 4., 4.1]), .5)
        np.testing.assert_array_equal(valid, [False, True, True, False, True, True, False])
        np.testing.assert_array_equal(x[valid], [10, 10, 20, 40])
        with self.assertRaises(ValueError):
            hold(np.array([1., 1.]), np.ones(2), np.array([1.]), .5)

    def test_known_delay_gain_and_offset_and_common_comparison(self):
        rng = np.random.default_rng(17)
        ct = np.arange(50, dtype=float)
        u = rng.normal(size=50)
        t = np.arange(3.125, 45, .25)
        delayed, _ = hold(ct, u, t-2, 2.)
        y = 1.7*delayed-.4
        result, profile, keep, _, prediction = fit_response(ct, u, t, y, np.arange(4.), 2.)
        self.assertEqual(result['delay_affine']['lag_s'], 2.)
        self.assertAlmostEqual(result['delay_affine']['gain'], 1.7)
        self.assertAlmostEqual(result['delay_affine']['offset_m_s'], -.4)
        np.testing.assert_allclose(prediction, y[keep], atol=1e-14)
        self.assertGreater(profile[0]['rmse_m_s'], .5)
        self.assertEqual(result['sample_count'], int(keep.sum()))

    def test_clock_duplicates_backwards_and_gap_are_visible(self):
        r = timing([0, 10, 20, 20, 15, 1000])
        self.assertEqual(r['duplicate_intervals'], 1)
        self.assertEqual(r['backward_intervals'], 1)
        self.assertEqual(r['gap_count'], 1)


if __name__ == '__main__':
    unittest.main()
