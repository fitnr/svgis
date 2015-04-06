from . import convert
from .draw import feature as draw

def scale(feature, factor=1):
    return {
        'properties': feature.get('properties'),
        'geometry': convert.scale_geometry(feature['geometry'], factor),
    }

def project(feature, projection):
    '''Apply a projection to the coordinates in a feature'''
    return {
        'properties': feature.get('properties'),
        'geometry': convert.project_geometry(feature['geometry'], projection)
    }
