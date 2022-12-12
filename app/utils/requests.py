from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
from flask import current_app as app
from scipy.stats import rv_continuous, rv_histogram, norm
from werkzeug.exceptions import BadRequest

from app.calculations.math import bins_boundaries, histogram
from app.utils.qc_strategy import QcStrategy
from app.utils.types import Histogram


def parse_test_point_distributions(testPoints: List[Dict[str, Any]], fit_to_dist: bool = True) -> \
        Union[List[rv_continuous], List[List[float]]]:
    """
    Parses the distribution of each given test point.

    Parameters
    ----------
    testPoints
        list where for every test point the json dict indicates a distribution that should be parsed.
    fit_to_dist
        true if the distribution should be fitted to a scipy.stats distribution.
        false if just all values from an empirical distribution should be returned.

    Returns
    -------
    Union[List[rv_continuous], List[List[float]]]
        depending on whether fit_to_dist is true or false, a list of scipy.stats distributions or a list of
        empirical values.
    """
    if fit_to_dist:
        return [parse_distribution(dist) for dist in testPoints]
    else:
        result = []
        for dist in testPoints:
            if dist["dist"] != "emp":
                raise BadRequest("All distributions must be of type emp!")
            result.append(dist["values"])
        # noinspection PyTypeChecker
        return np.array(result).transpose().tolist()


def parse_distribution(dic: Dict[str, Any]) -> rv_continuous:
    """
    Parses a distribution from an API request body.
    The distribution can be supplied directly or be fitted to another distribution.

    Parameters
    ----------
    dic
        {
            "dist": Union["emp", "hist", "norm"]
        }

    Returns
    -------
    rv_continuous
        a scipy distribution.

    Raises
    ------
    BadRequest
        if the distribution could not be parsed from the input arguments.
    """
    supported_distributions = {
        "emp": parse_emp,
        "hist": parse_hist,
        "norm": parse_norm,
    }
    dist = dic["dist"]
    if dist not in supported_distributions:
        raise BadRequest(f"unsupported distribution {dist}")

    return supported_distributions[dist](dic)


def parse_emp(dic: Dict[str, Any]) -> rv_continuous:
    """
    Tries to fit an empirical distribution to either a 2d histogram or (using MLE) a continuous distribution.

    Parameters
    ----------
    dic
        {
            "dist": "emp",
            "values": List[float],
            "fit": Union["norm", "hist"],
            "bins": float,
            "range": Tuple[float, float]
        }

    Returns
    -------
    rv_continuous
        a scipy distribution.

    Raises
    ------
    BadRequest
        if the distribution could not be parsed from the input arguments.
    """
    fit = dic["fit"]
    values = dic["values"]

    if fit == "hist":
        bins = dic["bins"]
        boundary = dic["range"]
        if not isinstance(boundary, list) or len(boundary) != 2:
            raise BadRequest("range param must be a list of len 2")

        return parse_array_as_hist(values, bins, tuple(boundary))
    else:
        supported_fit_methods = {
            "norm": norm,
        }
        if fit not in supported_fit_methods:
            raise BadRequest(f"unsupported fit method {fit}")

        dist = supported_fit_methods[fit]
        return dist.fit(values)


def parse_array_as_hist(values: List[float], bins: int, boundary: Tuple[float, float]) -> rv_histogram:
    """
    Parses a plain array as a histogram with given number of bins and bounds.

    Parameters
    ----------
    values
        values for the histogram.
    bins
        number of bins.
    boundary
        boundary of the histogram.

    Returns
    -------
    rv_histogram
        a scipy distribution.
    """
    x, y = histogram(np.array(values), bins, boundary)
    assert len(x) == bins + 1
    assert len(y) == bins
    return rv_histogram((y, x))


def parse_hist(dic: Dict[str, Any]) -> rv_histogram:
    """
    Parses a 2d histogram distribution.

    Parameters
    ----------
    dic
        {
            "dist": "hist",
            "x": List[float],
            "y": List[float],
        }

    Returns
    -------
    rv_histogram
        a scipy distribution.

    Raises
    ------
    BadRequest
        if the distribution could not be parsed from the input arguments.
    """
    x = dic["x"]
    y = dic["y"]
    if len(x) == len(y):
        x = bins_boundaries(np.array(x))
    elif len(x) != len(y) + 1:
        raise BadRequest("len(x) must be len(y) or len(y) + 1")

    return rv_histogram((y, x))


def parse_norm(dic: Dict[str, Any]) -> norm:
    """
    Parses a normal distribution.

    Parameters
    ----------
    dic
        {
            "dist": "norm",
            "mean": float,
            "std": float
        }

    Returns
    -------
    norm
        a scipy distribution.
    """
    mean = dic["mean"]
    std = dic["std"]

    return norm(loc=mean, scale=std)


def get_standard_convolution(standard_convolutions: List[Dict[str, Any]], components: List[str]) -> Optional[List[Histogram]]:
    """
    Find the standard convolution of the given component combination.

    Parameters
    ----------
    standard_convolutions
        standard convoluted distributions.
    components
        list of components whose convolution should be found.

    Returns
    -------
    Optional[List[Histogram]]
        If a standard convolution exists for the given components,
        then this method returns for every test point the histogram.
        Otherwise, this method returns None.
    """
    matches = [x["Distributions"] for x in standard_convolutions if set(x["Components"]) == set(components)]
    if len(matches) == 0:
        return None
    assert len(matches) == 1
    distributions = matches[0]
    return [(np.array(dic["x"]), np.array(dic["y"])) for dic in distributions]


def get_tolerances(config: str) -> List[Tuple[float, float]]:
    """
    Parameters
    ----------
    config
        name of the config that should be used for the tolerances.

    Returns
    -------
    List[Tuple[float, float]]
        for every test point, the lower and upper tolerances relative to its center.
    """
    test_point_names = app.config[config]["TestPoints"]
    return [v for k, v in app.config[config]["Tolerances"].items() if k in test_point_names]


def get_fulfillment_axis_range(tolerances: List[Tuple[float, float]], bins: int) -> List[Tuple[float, float]]:
    """
    Calculates the axis range for the resulting histogram fulfillment plots.

    Parameters
    ----------
    tolerances
        list of lower and upper bounds
    bins
        number of bins.

    Returns
    -------
    List[Tuple[float, float]]
        for every test point, the lower and upper axis bounds.
    """
    result = []
    for lower, upper in tolerances:
        width = upper - lower
        binWidth = width / (bins - 2)

        result.append((lower - binWidth, upper + binWidth))

    return result


def parse_qc_strategy(qc_strategy: str) -> Optional[QcStrategy]:
    """
    Parses the quality control strategy from the http request argument.

    Parameters
    ----------
    qc_strategy
        the request argument.

    Returns
    -------
    Optional[QcStrategy]
        parsed quality control strategy.
    """
    if qc_strategy == "":
        return None

    try:
        return QcStrategy[qc_strategy]
    except KeyError:
        raise BadRequest("Unknown qc strategy " + qc_strategy)
