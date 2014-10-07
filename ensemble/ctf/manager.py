from abc import abstractmethod
import glob
import os

from traits.api import ABCHasTraits, Dict, Instance, List, Str, Tuple

from .piecewise import PiecewiseFunction
from .utils import load_ctf, save_ctf


CTF_EXTENSION = '.ctf'


class ICtfManager(ABCHasTraits):
    """ Interface for managing a collection of CTFs by name.
    """

    # The available CTFs.
    names = List(Str)

    @abstractmethod
    def get(self, name):
        """ Return transfer functions for the given name.

        Parameters
        ----------
        name : str
            The name of the transfer function.

        Returns
        -------
        color_func : PiecewiseFunction
            The color transfer function.
        alpha_func : PiecewiseFunction
            The opacity transfer function.
        """

    @abstractmethod
    def add(self, name, color_func, alpha_func):
        """ Add a transfer function with the given name.

        Parameters
        ----------
        name : str
            The name of the transfer function.
        color_func : PiecewiseFunction
            The color component of the transfer function.
        alpha_func : PiecewiseFunction
            The opacity component of the transfer function.
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
    def from_directory(cls, root_dir, **traits):
        """ Create a new instance using the files in directory `root_dir`
        """
        manager = cls(root_dir=root_dir, **traits)
        manager._read_from_dir()
        return manager

    def add(self, name, ctf, otf):
        fn = os.path.join(self.root_dir, name + CTF_EXTENSION)
        save_ctf(ctf, otf, fn)
        self.functions[name] = (ctf.copy(), otf.copy())
        self._update_names()

    def get(self, name):
        return self.functions.get(name)

    def _read_from_dir(self):
        ctfs = glob.glob(os.path.join(self.root_dir, '*' + CTF_EXTENSION))
        funcs = {}
        for fn in ctfs:
            name = os.path.splitext(os.path.basename(fn))[0]
            funcs[name] = load_ctf(fn)
        self.functions = funcs
        self._update_names()

    def _update_names(self):
        self.names = sorted(self.functions)
