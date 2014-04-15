import os
import glob

from traits.api import ABCHasTraits, Dict, Instance, List, Str, Tuple

from ensemble.ctf.utils import load_ctf, save_ctf
from ensemble.ctf.piecewise import PiecewiseFunction


EXTENSION = '.ctf'


class ICtfManager(ABCHasTraits):
    """ Interface for managing a collection of CTFs by name.
    """

    # The available CTFs.
    names = List(Str)

    def get(self, name):
        """ Return transfer functions for the given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        ctf : PiecewiseFunction
            The color transfer function.
        otf : PiecewiseFunction
            The opacity transfer function.
        """

    def add(self, name, ctf, otf):
        """ Add transfer functions with the given name.

        Parameters
        ----------
        name : str
        ctf : PiecewiseFunction
        otf : PiecewiseFunction
        """


class CtfManager(ICtfManager):
    """ Simple manager for loading and saving CTF files to a directory.
    """

    # The root directory with the files.
    root_dir = Str('.')

    # The transfer functions by name.
    functions = Dict(
        Str,
        Tuple(Instance(PiecewiseFunction), Instance(PiecewiseFunction)),
    )

    @classmethod
    def fromdir(cls, root_dir, **traits):
        self = cls(root_dir=root_dir, **traits)
        self.read_from_dir()
        return self

    def read_from_dir(self):
        ctfs = glob.glob(os.path.join(self.root_dir, '*' + EXTENSION))
        funcs = {}
        for fn in ctfs:
            name = os.path.splitext(os.path.basename(fn))[0]
            funcs[name] = load_ctf(fn)
        self.functions = funcs
        self._update_names()

    def add(self, name, ctf, otf):
        fn = os.path.join(self.root_dir, name + EXTENSION)
        save_ctf(ctf, otf, fn)
        self.functions[name] = (ctf.copy(), otf.copy())
        self._update_names()

    def get(self, name):
        return self.functions.get(name)

    def _update_names(self):
        self.names = sorted(self.functions)
