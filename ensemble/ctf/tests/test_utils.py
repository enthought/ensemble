import unittest

import numpy as np
from numpy.testing import assert_array_equal

from ensemble.ctf.utils import trapezoid_window


class TestTrapezoidWindow(unittest.TestCase):

    def test_empty_window(self):
        w = trapezoid_window(0)
        assert_array_equal(w, np.array([]))

    def test_basic_window(self):
        w = trapezoid_window(5)
        window_start = w[0]
        window_center = w[1:4]
        window_stop = w[4]

        assert_array_equal(window_center, np.ones((3)))
        self.assertEqual(window_start, 0)
        self.assertEqual(window_stop, 0)
