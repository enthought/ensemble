from __future__ import unicode_literals
import json

import numpy as np

from .transfer_function import TransferFunction


def build_screen_to_function(component):
    def func(pos):
        bounds = component.bounds
        return tuple([clip_to_unit(z / size) for z, size in zip(pos, bounds)])
    return func


def clip_to_unit(value):
    return clip(value, (0.0, 1.0))


def clip(value, limits):
    v_min, v_max = limits
    return min(max(value, v_min), v_max)


def load_ctf(filename):
    """ Load a TransferFunction from a file.
    """
    with open(filename, 'rb') as fp:
        loaded_data = json.load(fp)
    return TransferFunction.from_dict(loaded_data)


def save_ctf(transfer_func, filename):
    """ Save a TransferFunction to a file.
    """
    function_data = transfer_func.to_dict()
    with open(filename, 'wb') as fp:
        json.dump(function_data, fp, indent=1)


def trapezoid_window(num_points):
    """ Return a window where endpoints are 0 and all other points are 1.0.

    Similar to boxcar or rectangular window in ``scipy.signal`` but with
    endpoints of 0.

    Parameters
    ----------
    num_points : int
        Number of points in the output window. If zero or less, an empty array
        is returned.
    """
    if num_points <= 0:
        return np.array([], dtype='float64')
    w = np.ones(num_points, dtype='float64')

    # Set endpoints of window
    w[0] = 0
    w[-1] = 0
    return w
