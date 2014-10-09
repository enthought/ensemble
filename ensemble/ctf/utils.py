from abc import abstractmethod
import json
from math import sqrt

import numpy as np

from enable.component import Component
from traits.api import ABCHasTraits, Callable, Float, Instance

from ensemble.ctf.piecewise import PiecewiseFunction, verify_values


def build_function_to_screen(component):
    def func(pos):
        bounds = component.bounds
        padding_left_bottom = [component.padding_left,
                               component.padding_bottom]
        return tuple([clip_to_unit(z) * size + padding
                      for z, size, padding in
                      zip(pos, bounds, padding_left_bottom)])
    return func


def build_screen_to_function(component):
    def func(pos):
        bounds = component.bounds
        padding_left_bottom = [component.padding_left,
                               component.padding_bottom]
        return tuple([clip_to_unit((z - padding) / size)
                      for z, size, padding in
                      zip(pos, bounds, padding_left_bottom)])
    return func


def clip_to_unit(value):
    return clip(value, (0.0, 1.0))


def clip(value, limits):
    v_min, v_max = limits
    return min(max(value, v_min), v_max)


def dist2d(pos0, pos1):
    diff = np.subtract(pos0, pos1)
    return sqrt(diff[0]**2 + diff[1]**2)


def load_ctf(filename):
    """ Load transfer functions from a file.
    """
    with open(filename, 'rb') as fp:
        loaded_data = json.load(fp)

    keys = ('alpha', 'color')
    has_values = all(k in loaded_data for k in keys)
    verified_values = all(verify_values(loaded_data[k]) for k in keys)
    if not (has_values and verified_values):
        msg = "{0} does not have valid transfer function data."
        raise IOError(msg.format(filename))

    alpha_func = PiecewiseFunction()
    color_func = PiecewiseFunction()
    parts = (('alpha', alpha_func), ('color', color_func))
    for name, func in parts:
        for value in loaded_data[name]:
            func.insert(tuple(value))

    return (color_func, alpha_func)


def save_ctf(color_func, alpha_func, filename):
    """ Save transfer functions to a file.
    """
    function = {'alpha': alpha_func.values(), 'color': color_func.values()}
    with open(filename, 'wb') as fp:
        json.dump(function, fp, indent=1)


class FunctionUIAdapter(ABCHasTraits):
    """ A class to handle translation between screen space and function space
    """
    # The Component where the function lives
    component = Instance(Component)

    # The function being adapted
    function = Instance(PiecewiseFunction)

    # A function which maps a point from function space to screen space
    function_to_screen = Callable

    # A function which maps a point from screen space to function space
    screen_to_function = Callable

    def _function_to_screen_default(self):
        return build_function_to_screen(self.component)

    def _screen_to_function_default(self):
        return build_screen_to_function(self.component)

    @abstractmethod
    def function_index_at_position(self, x, y):
        """ Implemented by subclasses to find function nodes at the given
        mouse position. Returns None if no node is found.
        """


class AlphaFunctionUIAdapter(FunctionUIAdapter):
    """ UI adapter for the alpha function
    """
    # Maximum distance from a point in screen space to be considered valid.
    valid_distance = Float(8.0)

    def function_index_at_position(self, x, y):
        mouse_pos = (x, y)
        data_pos = self.screen_to_function(mouse_pos)
        indices = self.function.neighbor_indices(data_pos[0])
        values = [self.function.value_at(i) for i in indices]
        for index, val in zip(indices, values):
            val_screen = self.function_to_screen(val)
            if dist2d(val_screen, mouse_pos) < self.valid_distance:
                return index
        return None


class ColorFunctionUIAdapter(FunctionUIAdapter):
    """ UI adapter for the color function
    """
    # Maximum distance from a point in screen space to be considered valid.
    valid_distance = Float(5.0)

    def function_index_at_position(self, x, y):
        data_x = self.screen_to_function((x, y))[0]
        indices = self.function.neighbor_indices(data_x)
        values = [self.function.value_at(i) for i in indices]
        for index, val in zip(indices, values):
            val_screen = self.function_to_screen(val)[0]
            if abs(val_screen - x) < self.valid_distance:
                return index
        return None
