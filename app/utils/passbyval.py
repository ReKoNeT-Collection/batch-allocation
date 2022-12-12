from copy import deepcopy


def passbyval(func):
    """
    Makes a (deep) copy of all supplied parameters of the annotated function.

    Parameters
    ----------
    func
        the function that should be marked as pass-by-value

    Returns
    -------
    new
        new function where the parameters get copied first.
    """
    def new(*args):
        cargs = [deepcopy(arg) for arg in args]
        return func(*cargs)
    return new
