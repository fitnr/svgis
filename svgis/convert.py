import math
try:
    import numpy as np
except ImportError:
    pass


def rect(length, angle):
    '''polar to cartesian coordinates'''
    return length * math.cos(angle), length * math.sin(angle)


def scale_geometry(geometry, factor=1):
    coordinates = geometry['coordinates']

    if geometry['type'] == 'MultiPolygon':
        c = [scale_rings(rings, factor) for rings in coordinates]

    elif geometry['type'] in ('Polygon', 'MultiLineString'):
        c = scale_rings(coordinates, factor)

    elif geometry['type'] in ('MultiPoint', 'LineString'):
        c = scale(coordinates, factor)

    elif geometry['type'] == 'Point':
        c = scale(coordinates, factor)

    else:
        raise NotImplementedError("Unknown geometry type")

    return {
        'type': geometry['type'],
        'coordinates': c
    }


def scale_rings(rings, factor=1):
    return [scale(ring, factor) for ring in rings]


def scale(coordinates, scalar=1):
    '''Scale a list of coordinates by a scalar. Only use of projected coordinates'''
    try:
        return np.array(coordinates, dtype=float) * scalar
    except NameError:
        if isinstance(coordinates, tuple):
            return (coordinates[0] * scalar, coordinates[1] * scalar)

        return ((x * scalar, y * scalar) for x, y in coordinates)


def project(coordinates, projection):
    '''Project a list of coordinates'''
    return zip(*projection(zip(*coordinates)))


def project_rings(rings, projection):
    '''Apply a projection to rings in a geometry'''
    return [zip(*projection(*zip(*ring))) for ring in rings]


def project_geometry(geometry, projection):
    coordinates = geometry['coordinates']

    if geometry['type'] == 'MultiPolygon':
        c = [project_rings(rings, projection) for rings in coordinates]

    elif geometry['type'] in ('Polygon', 'MultiLineString'):
        c = project_rings(coordinates, projection)

    elif geometry['type'] in ('MultiPoint', 'LineString'):
        c = project(coordinates, projection)

    elif geometry['type'] == 'Point':
        c = projection(*coordinates)

    else:
        raise NotImplementedError("Unknown geometry type")

    return {
        'type': geometry['type'],
        'coordinates': c
    }
