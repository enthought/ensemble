from contextlib import contextmanager
from os.path import isfile, join
import shutil
import tempfile

from numpy.testing import assert_allclose

from ensemble.ctf.editor import ALPHA_DEFAULT, COLOR_DEFAULT, create_function
from ensemble.ctf.manager import CTF_EXTENSION, CtfManager


@contextmanager
def temp_directory():
    tempdir = tempfile.mkdtemp(suffix='', prefix='tmp', dir=None)
    try:
        yield tempdir
    finally:
        shutil.rmtree(tempdir)


def sample_function_parts():
    return create_function(COLOR_DEFAULT), create_function(ALPHA_DEFAULT)


def test_ctf_manager_add():
    name = 'test_function'
    color_func, alpha_func = sample_function_parts()

    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)
        manager.add(name, color_func, alpha_func)

        assert isfile(join(root_dir, name + CTF_EXTENSION))


def test_ctf_manager_get():
    color_func, alpha_func = sample_function_parts()

    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)
        manager.add('test', color_func, alpha_func)

        ret_color, ret_alpha = manager.get('test')
        assert_allclose(ret_color.values(), COLOR_DEFAULT)
        assert_allclose(ret_alpha.values(), ALPHA_DEFAULT)


def test_ctf_manager_load():
    color_func, alpha_func = sample_function_parts()

    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)
        manager.add('test', color_func, alpha_func)

        del manager
        manager = CtfManager.from_directory(root_dir)
        manager.get('test')
