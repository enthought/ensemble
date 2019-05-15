# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from contextlib import contextmanager
from os import listdir
import shutil
import tempfile

from numpy.testing import assert_allclose

from ensemble.ctf.api import CtfManager, TransferFunction


@contextmanager
def temp_directory():
    tempdir = tempfile.mkdtemp(suffix='', prefix='tmp', dir=None)
    try:
        yield tempdir
    finally:
        shutil.rmtree(tempdir)


def test_ctf_manager_add():
    transfer_func = TransferFunction()

    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)
        for i in range(5):
            manager.add(str(i), transfer_func)

        assert len(listdir(root_dir)) == 5


def test_ctf_manager_get():
    transfer_func = TransferFunction()

    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)
        manager.add('test', transfer_func)

        ret_func = manager.get('test')
        assert_allclose(ret_func.color.values(), transfer_func.color.values())
        assert_allclose(ret_func.opacity.values(),
                        transfer_func.opacity.values())


def test_ctf_manager_load():
    transfer_func = TransferFunction()

    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)
        manager.add('test', transfer_func)

        del manager
        manager = CtfManager.from_directory(root_dir)
        manager.get('test')


def _test_ctf_manager_names(names_to_test):
    transfer_func = TransferFunction()
    with temp_directory() as root_dir:
        manager = CtfManager.from_directory(root_dir)

        for name in names_to_test:
            manager.add(name, transfer_func)

        # Reload and check the names
        manager = CtfManager.from_directory(root_dir)
        for name in manager.names:
            assert name in names_to_test


def test_ctf_manager_crazy_names():
    # Handle unicode and slashes
    crazy_names = ['他妈的！// what?', '/this/looks/like/a/path/Ø']
    _test_ctf_manager_names(crazy_names)


def test_ctf_manager_padded_names():
    # Handle names which encode to a string which must be padded
    odd_length_names = ['1' * i for i in range(1, 4)]
    _test_ctf_manager_names(odd_length_names)
