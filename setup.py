# -*- coding: utf-8 -*-

"""
To upload to PyPI, PyPI test, or a local server:
python setup.py bdist_wheel upload -r <server_identifier>
"""

import setuptools
import os

setuptools.setup(
    name="getdpc",
    version="0.1.0",
    author="Jordan Hachtel",
    description="GetDPC package",
    packages=["getdpc", "nionswift_plugin.getdpc"],
    install_requires=["matplotlib", "numpy", "scipy"],
    python_requires='~=3.6',
)
