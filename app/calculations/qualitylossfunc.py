from typing import Tuple, Union

import numpy as np

from app.calculations.math import bins_center
from app.utils.types import Histogram


def calculate_quality_loss(mean: Union[float, np.ndarray], target_mean: float, inefficiency_costs: float,
                           tolerance: Tuple[float, float]) -> Union[float, np.ndarray]:
    """
    Calculates the quality loss for the given value with respect to the target mean value.

    Parameters
    ----------
    mean
        current value.
    target_mean
        optimal value, where the loss is zero.
    inefficiency_costs
        costs per non-conforming unit, resulting from depreciation, scrap and rework.
    tolerance
        lower and upper tolerances.

    Returns
    -------
    Union[float, np.ndarray]
        the quality loss for the convolution of all given distributions.
    """
    allowed_deviation = np.abs(tolerance).mean()
    k = inefficiency_costs / (allowed_deviation ** 2)
    return k * (mean - target_mean) ** 2


def calculate_quality_loss_discrete(distribution: Histogram, target_mean: float,
                                    inefficiency_costs: float, tolerance: Tuple[float, float]) -> float:
    """
    Calculates the quality loss for the given probability distributions with respect to the target mean value.

    Parameters
    ----------
    distribution
        histogram of a probability distribution. All y values must add up to 1.
    target_mean
        mean of the standard distribution.
    inefficiency_costs
        costs per non-conforming unit, resulting from depreciation, scrap and rework.
    tolerance
        lower and upper tolerances.

    Returns
    -------
    float
        the quality loss for the convolution of all given distributions.
    """
    y, x = distribution
    y /= y.sum()
    y = y * calculate_quality_loss(bins_center(x), target_mean, inefficiency_costs, tolerance)
    return y.sum()
