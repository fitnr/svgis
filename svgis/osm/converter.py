# -*- coding: utf-8 -*-

# This file is part of svgis.
# https://github.com/fitnr/svgis

# Licensed under the GNU General Public License v3 (GPLv3) license:
# http://opensource.org/licenses/GPL-3.0
# Copyright (c) 2015, Neil Freeman <contact@fakeisthenewreal.org>

"""Draw OSM geometries as SVG"""

from __future__ import division, print_function
import svgwrite
from fiona.transform import transform
from .. import projection
from .. import draw as svgisdraw


def draw(osm, scalar=None, bounds=None, out_crs=None, **kwargs):
    """
    Draw ways in a OSM file
    :osm An OSM wrapper object
    """

    out_crs = make_projection(osm, out_crs)
    project = lambda xs, ys: transform('EPSG:4326', out_crs, xs, ys)

    group = svgwrite.container.Group(id=osm.id)

    for geom in osm.geometries(project, scalar=scalar, bounds=bounds):
        if geom:
            group.add(svgisdraw.geometry(geom, **kwargs))

    return group


def make_projection(osm, out_crs=None):
    if out_crs is None:
        coords = [(float(n.get('lon')), float(n.get('lat'))) for n in osm.nodes()]
        lons, lats = zip(*coords)

        midx = (max(lons) + min(lons)) / 2
        midy = (max(lats) + min(lats)) / 2

        out_crs = projection.utm_proj4(midx, midy)

    return out_crs
