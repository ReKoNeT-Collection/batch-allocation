from typing import List

import numpy as np
import pandas as pd
from flask import current_app as app
from werkzeug.exceptions import BadRequest

from app.calculations.functional_models import regression
from app.utils.types import Component


def get_batch_function(characteristic_values: pd.DataFrame, config: str, weighted: bool = False) -> pd.DataFrame:
    """
    Calculates the functional fulfillment of the given characteristic values.

    Parameters
    ----------
    characteristic_values
        a pandas data frame where the columns represent the characteristic values and each row is a single entry.
    config
        name of the configuration that should be used for the functional model.
    weighted
        True if another column should be returned with a weighted fulfillment over all test points.

    Returns
    -------
    pd.DataFrame
        a pandas data frame where each column y represents a test point and each row x represents the functional
        fulfillment of the x-th entry and the y-th test point.
    """
    means = app.config[config]["MeanValues"]
    if config == "test" or config == "dummy":
        functional_model = app.config[config]["FunctionalModel"]
        result = regression.calculate_batch(characteristic_values, functional_model, means)
    else:
        raise BadRequest("unsupported configuration " + config)
    if weighted:
        # calculate weighted test point
        weights = app.config[config]["TestPointWeights"]
        result["weighted"] = np.average(result, weights=weights, axis=1)

    return result


def get_function(characteristic_values: Component, config: str, weighted: bool = False) -> List[float]:
    """
    Calculates the functional fulfillment of the given characteristic values.

    Parameters
    ----------
    characteristic_values
        a dictionary where the columns represent the characteristic values and each row is a single entry.
    config
        name of the configuration that should be used for the functional model.
    weighted
        True if another column should be returned with a weighted fulfillment over all test points.

    Returns
    -------
    List[float]
        the functional fulfillment of the item for each test point.
    """
    means = app.config[config]["MeanValues"]
    if config == "test" or config == "dummy":
        functional_model = app.config[config]["FunctionalModel"]
        result = regression.calculate(characteristic_values, functional_model, means)
    else:
        raise BadRequest("unsupported configuration " + config)
    if weighted:
        # calculate weighted test point
        weights = app.config[config]["TestPointWeights"]
        result.append(np.average(result, weights=weights))

    return result
