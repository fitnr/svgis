#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

from setuptools import setup, find_packages

setup(
    name='svgis',

    version='0.1.0',

    description='Draw geodata in SVG',

    long_description='''Draw geodata in SVG''',

    keywords='svg gis geojson shapefile',

    author='Neil Freeman',

    author_email='contact@fakeisthenewreal.org',

    url='https://github.com/fitnr/svgis',

    license='GNU General Public License v3 (GPLv3)',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3) License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Operating System :: OS Independent',
    ],

    packages=find_packages(),

    include_package_data=False,

    install_requires=[
        'pyproj>=1.9.3,<1.10',
        'fiona>=1.5.0,<2.0',
        'svgwrite>=1.1.6,<1.2',
        'fionautil>=0.1.0,<1.0',
    ],

    tests_require=['tox'],

    test_suite='tests',

    entry_points={
        'console_scripts': [
            'svgis=svgis.cli:main',
        ],
    },
)
