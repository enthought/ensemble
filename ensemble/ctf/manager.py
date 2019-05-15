from base64 import urlsafe_b64encode, urlsafe_b64decode
import glob
import os

from traits.api import HasStrictTraits, Dict, Instance, List, Unicode

from .transfer_function import TransferFunction
from .utils import load_ctf, save_ctf


CTF_EXTENSION = '.ctf'


def _name_encode(name):
    return urlsafe_b64encode(name.encode('utf-8'))


def _name_decode(name):
    return urlsafe_b64decode(name).decode('utf-8')


class CtfManager(HasStrictTraits):
    """ Simple manager for loading and saving CTF files to a directory.
    """

    # The root directory with the files.
    root_dir = Unicode('.')

    # The available CTFs.
    names = List(Unicode)

    # The transfer functions by name.
    functions = Dict(Unicode, Instance(TransferFunction))

    @classmethod
    def from_directory(cls, root_dir, **traits):
        """ Create a new instance using the files in directory `root_dir`
        """
        manager = cls(root_dir=root_dir, **traits)
        manager._read_from_dir()
        return manager

    def add(self, name, transfer_func):
        """ Add a transfer function with the given name.

        Parameters
        ----------
        name : str
            The name of the transfer function.
        transfer_func : TransferFunction
            A transfer function instance
        """
        encoded_name = _name_encode(name)
        fn = os.path.join(self.root_dir, encoded_name + CTF_EXTENSION)
        if not os.path.isdir(self.root_dir):
            os.makedirs(self.root_dir)

        save_ctf(transfer_func, fn)
        self.functions[name] = transfer_func
        self._update_names()

    def get(self, name):
        """ Return a function for the given name.

        Parameters
        ----------
        name : str
            The name of the function.

        Returns
        -------
        transfer_func : TransferFunction
            A transfer function.
        """
        return self.functions.get(name).copy()

    def _read_from_dir(self):
        ctfs = glob.glob(os.path.join(self.root_dir, '*' + CTF_EXTENSION))
        funcs = {}
        for fn in ctfs:
            name = os.path.splitext(os.path.basename(fn))[0]
            decoded_name = _name_decode(name)
            funcs[decoded_name] = load_ctf(fn)
        self.functions = funcs
        self._update_names()

    def _update_names(self):
        self.names = sorted(self.functions)
