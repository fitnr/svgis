#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

from setuptools import setup

try:
    readme = open('README.md').read()
except IOError:
    readme = ''

with open('svgis/__init__.py') as i:
    version = next(r for r in i.readlines() if '__version__' in r).split('=')[1].strip('"\' \n')

setup(
    name='svgis',
    version=version,
    description='Draw geodata in SVG',
    long_description=readme,
    long_description_content_type='text/markdown',
    keywords='svg gis geojson shapefile',
    author='Neil Freeman',
    author_email='contact@fakeisthenewreal.org',
    url='https://github.com/fitnr/svgis',
    license='GNU General Public License v3 (GPLv3)',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
    ],
    packages=['svgis'],
    install_requires=[
        'six>=1.7.3,<2',
        'click>=6.2,<8',
        'pyproj>=1.9.5,<2',
        'fiona>=1.8,<2.0',
        'fionautil>=0.6,<1.0',
        'tinycss==0.3',
        'utm>=0.4.0,<1'
    ],
    extras_require={
        'numpy': [''],
        'clip': ['shapely>=1.5.7'],
        'inline': [],
        'simplify': ['visvalingamwyatt>=0.1.1']
    },
    test_suite='tests',
    tests_require=['six'],
    entry_points={
        'console_scripts': [
            'svgis=svgis.cli:main',
        ],
    },
)
