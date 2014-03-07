# Copyright (c) 2014 by Enthought, Inc.
# All rights reserved.

import os.path
from setuptools import setup, find_packages

d = {}
execfile(os.path.join('ensemble', '__init__.py'), d)

setup(
    name='ensemble',
    version=d['__version__'],
    author='Enthought, Inc',
    author_email='info@enthought.com',
    url='https://github.com/enthought/ensemble',
    description='High-level widgets for building Python applications',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=('*.tests',)),
    requires=[],
)
