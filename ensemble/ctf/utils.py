import json

from .linked import LinkedFunction


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
    """ Load a LinkedFunction from a file.
    """
    with open(filename, 'rb') as fp:
        loaded_data = json.load(fp)
    return LinkedFunction.from_dict(loaded_data)


def save_ctf(linked_func, filename):
    """ Save a LinkedFunction to a file.
    """
    function_data = linked_func.to_dict()
    with open(filename, 'wb') as fp:
        json.dump(function_data, fp, indent=1)
