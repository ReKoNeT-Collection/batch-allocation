from typing import List, Dict

import numpy as np
import pandas as pd
from werkzeug.exceptions import BadRequest

from app.utils.types import Component


def calculate_batch(characteristic_values: pd.DataFrame, functional_model: Dict[str, List[float]],
                    means: Dict[str, float]) -> pd.DataFrame:
    """
    Calculates the linear function of multiple values at once.

    Parameters
    ----------
    characteristic_values
        a pandas data frame where the columns represent the characteristic values and each row is a single entry.
    functional_model
        a linear regression model in dictionary where the columns represent the test points and the rows
        represent the characteristic values.
    means
        a dictionary where for each characteristic value the mean is assigned to.

    Returns
    -------
    pd.DataFrame
        a pandas data frame where each column y represents a test point and each row x represents the functional
        fulfillment of the x-th entry and the y-th test point.
    """
    coef_names = list(functional_model.keys())
    n_points = len(functional_model[coef_names[0]])
    result = pd.DataFrame(np.empty((len(characteristic_values), n_points)))

    # create an intersection between the saved config values and the request values
    # and sort the resulting specified_values list
    specified_values = list(set(coef_names).intersection(characteristic_values.columns))
    if len(specified_values) == 0:
        raise BadRequest(f"No functional values specified!")
    # filter data to only calculate the fulfillment of the specified values
    characteristic_values = characteristic_values[specified_values]
    # make means the same order as characteristic values.
    means = [means[key] for key in characteristic_values.keys()]

    # calculate fulfillment values for each test point
    for i in range(n_points):
        # order the coefficients alphabetically so that the order matches with the
        # order of columns in the characteristic_values data frame
        coeffs = [functional_model[key][i] for key in characteristic_values.keys()]
        # calculate the sum-product as follows:
        # (characteristicValue_1 - mu) * coef_1 + ... + (characteristicValue_n - mu) * coef_n
        result.iloc[:, i] = ((characteristic_values - means) * coeffs).sum(axis=1)
    return result


def calculate(characteristic_values: Component, functional_model: Dict[str, List[float]],
              means: Dict[str, float]) -> List[float]:
    """
    Calculates the linear function for a single item.

    Parameters
    ----------
    characteristic_values
        a dictionary where the columns represent the characteristic values and each row is a single entry.
    functional_model
        a linear regression model in dictionary where the columns represent the test points and the rows
        represent the characteristic values.
    means
        a dictionary where for each characteristic value the mean is assigned to.

    Returns
    -------
    List[float]
        the functional fulfillment of the item for each test point.
    """
    coef_names = list(functional_model.keys())
    n_points = len(functional_model[coef_names[0]])

    # make means the same order as characteristic values.
    means = np.array([means[key] for key in characteristic_values.keys()])
    characteristic_values_arr = np.array(list(characteristic_values.values()))

    result = []
    # calculate fulfillment values for each test point
    for i in range(n_points):
        # order the coefficients alphabetically so that the order matches with the
        # order of columns in the characteristic_values data frame
        coeffs = np.array([functional_model[key][i] for key in characteristic_values.keys()])
        # calculate the sum-product as follows:
        # (characteristicValue_1 - mu) * coef_1 + ... + (characteristicValue_n - mu) * coef_n
        result.append(((characteristic_values_arr - means) * coeffs).sum())
    return result
