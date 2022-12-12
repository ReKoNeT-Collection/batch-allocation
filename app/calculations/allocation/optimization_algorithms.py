####################################################################
# OPTIMIZATION ALGORITHMS                                          #
####################################################################
from typing import List, Any, Dict, Tuple, Callable

import numpy as np
import pandas as pd
from flask import current_app as app

from app.calculations.allocation.convolution_methods import ConvolutionMethod
from app.calculations.allocation.valuation_methods import ValuationMethod
from app.calculations.optimization import brute_force


def evaluate_batches(batches_a: pd.DataFrame, batches_b: pd.DataFrame, convolution_method: ConvolutionMethod,
                     valuation_method: ValuationMethod,
                     settings_dict: Dict[str, Any]) -> float:
    """
    Evaluates two given batches and calculates a value, which will be used for optimization.

    Parameters
    ----------
    batches_a
        Distribution of components in batch a.
    batches_b
        Distribution of components in batch b.
    convolution_method
        Method for convolution of two distributions.
    valuation_method
        Method for converting a distribution into a scalar value.
    settings_dict
        Optional settings.

    Returns
    -------
    float
        scalar value for this batch combination.
    """
    # Simulate assembly of all components + calculation of functional fulfillment for each test point.
    distributions = convolution_method(batches_a, batches_b, settings_dict)
    # Apply method for converting a distribution into a scalar value
    scalars = [valuation_method(distributions[test_point], test_point, settings_dict) for test_point in
               range(len(distributions))]
    weights = app.config[settings_dict["config"]]["TestPointWeights"]
    return np.average(scalars, weights=weights)


def apply_brute_force(components: Tuple[List[pd.DataFrame], List[pd.DataFrame]], convolution_method: ConvolutionMethod,
                      valuation_method: ValuationMethod, settings_dict: Dict[str, Any]) -> Tuple[List[int], List[float]]:
    """
    Uses brute-force optimization to find the best allocation.

    Parameters
    ----------
    components
        array containing two different lists, whose elements should be evaluated against each other.
    convolution_method
        Method for convolution of two distributions.
    valuation_method
        method for converting a distribution into a scalar value.
    settings_dict
        Optional settings.

    Returns
    -------
    List[int]
        optimal allocation sequence.
    List[float]
        scalar values for this batch combination.
    """
    return brute_force(components,
                       lambda batch_a, batch_b: evaluate_batches(batch_a, batch_b, convolution_method, valuation_method,
                                                                 settings_dict))


OptimizationAlgorithm = Callable[
    [Tuple[List[pd.DataFrame], List[pd.DataFrame]], ConvolutionMethod, ValuationMethod, Dict[str, Any]], Tuple[
        List[int], List[float]]]

supported_algorithms: Dict[str, OptimizationAlgorithm] = {
    "brute_force": apply_brute_force,
}
