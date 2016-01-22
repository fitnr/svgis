from __future__ import unicode_literals
from .errors import SvgisError
try:
    import numpy as np
except ImportError:
    pass

def databins(features, prop, n, method):
    '''
    :features Sequence A sequence of GeoJSON-like features.
    :property property to examine.
    :n int Number of data bins to create.
    :method string "quantile", "interval" (for equal interval).
    '''
    values = [f['properties'].get(prop) for f in features]

    if not any(values):
        raise SvgisError("No values found for field: %s" % prop)

    return _databins(values, n, method)

def _databins(values, n, method):
    '''
    :values Sequence Values to base bins upon.
    :n int Number of bins to return
    :method string "quantile", "interval" (for equal interval).
    '''
    x = 100 / float(n)
    breaks = list(range(x, 101, x))

    if method == "quantile":

        try:
            bins = np.percentile(values, breaks)
        except NameError:
            return _databins(values, n, "interval")

    else:
        values.sort()
        l = len(values)
        bins = [values[int(i * l * 0.01)-1] for i in breaks]

    return bins

def binner(bins, binformat=None):
    '''
    Returns a function that checks which bin a value falls in.
    :bins Sequence Values that give the upper bound of bins. Last value should equal the max of the dataset
    :binformat string A string that will accept two values in the format method:
                      the bin number (0, n-1) and the number of bins (n). Default: q-{}-{}.
    '''
    binformat = binformat or "q-{}-{}"
    L = len(bins)

    def func(value):
        B = len([b for b in bins if b <= value])

        return binformat.format(B, L)

    return func
