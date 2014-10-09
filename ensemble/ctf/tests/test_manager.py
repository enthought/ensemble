# -*- coding: utf-8 -*-

from contextlib import contextmanager
from os import listdir
import shutil
import tempfile

from numpy.testing import assert_allclose

from ensemble.ctf.editor import ALPHA_DEFAULT, COLOR_DEFAULT, create_function
from ensemble.ctf.manager import CtfManager


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
    color_func, alpha_func = sample_function_parts()

    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)
        for i in range(5):
            manager.add(str(i), color_func, alpha_func)

        assert len(listdir(root_dir)) == 5


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


def _test_ctf_manager_names(names_to_test):
    color_func, alpha_func = sample_function_parts()
    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)

        for name in names_to_test:
            manager.add(name, color_func, alpha_func)

        # Reload and check the names
        manager = CtfManager.from_directory(root_dir)
        for name in manager.names:
            assert name in names_to_test


def test_ctf_manager_crazy_names():
    # Handle unicode and slashes
    crazy_names = [u'他妈的！// what?', u'/this/looks/like/a/path/Ø']
    _test_ctf_manager_names(crazy_names)


def test_ctf_manager_padded_names():
    # Handle names which encode to a string which must be padded
    odd_length_names = ['1' * i for i in range(1, 4)]
    _test_ctf_manager_names(odd_length_names)
