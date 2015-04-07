import math


def rect(length, angle):
    '''polar to cartesian coordinates'''
    return length * math.cos(angle), length * math.sin(angle)

def replacebounds(bounds1, bounds2):
    '''Replace any missing min/max points in bounds1 with from bounds2'''
    if any(not v for v in bounds1):
        bounds1 = [(a or b) for a, b in zip(bounds1, bounds2)]

    return bounds1
