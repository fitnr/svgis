#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

from setuptools import setup

try:
    readme = open('README.rst').read()
except IOError:
    readme = ''

setup(
    name='svgis',

    version='0.3.1',

    description='Draw geodata in SVG',

    long_description=readme,

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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: OS Independent',
    ],

    packages=['svgis', 'svgis.cli'],

    package_data={
        'svgis': ['test_data/test.*']
    },

    install_requires=[
        'pyproj>=1.9.5,<1.10',
        'fiona>=1.6.0,<2.0',
        'fionautil >=0.4.6, <1.0',
        'utm>=0.4.0,<1'
    ],

    extras_require={
        'numpy': ['numpy'],
        'clip': ['shapely>=1.5.7'],
        'inline': [
            'cssselect>=0.9.1,<1',
            'tinycss>=0.3,<0.4',
            'lxml>=3.5.0,<4.0',
        ],
        'simplify': ['visvalingamwyatt>=0.1.1']
    },

    test_suite='tests',

    entry_points={
        'console_scripts': [
            'svgis=svgis.cli:main',
        ],
    },

    use_2to3=True,
)
