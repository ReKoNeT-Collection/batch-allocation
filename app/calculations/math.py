from dataclasses import dataclass
from typing import Union, Tuple

import numpy as np
from scipy.stats import rv_continuous

from app.utils.types import Histogram


@dataclass
class AnyDistribution:
    """
    Represents a generic distribution.
    """
    _mean: float
    _std: float

    def mean(self):
        return self._mean

    def std(self):
        return self._std

    def conv(self, other: "AnyDistribution") -> "AnyDistribution":
        """
        Convolution with another distribution.

        Parameters
        ----------
        other
            the other distribution that should be convoluted.

        Returns
        -------
        AnyDistribution
            the convoluted distribution.
        """
        return AnyDistribution(self._mean + other._mean, np.sqrt(self._std ** 2 + other._std ** 2))

    def __add__(self, other):
        return self.conv(other)

    @staticmethod
    def from_rv_continuous(distribution: rv_continuous) -> "AnyDistribution":
        return AnyDistribution(distribution.mean(), distribution.std())

    @staticmethod
    def from_ndarray(distribution: np.ndarray) -> "AnyDistribution":
        return AnyDistribution(distribution.mean(), distribution.std())


def normalized_mean(distribution: np.ndarray, lower_tolerance: float, upper_tolerance: float):
    return distribution.mean() / (upper_tolerance - lower_tolerance)


def normalized_mean_std(distribution: np.ndarray, lower_tolerance: float, upper_tolerance: float):
    return (distribution.mean() + distribution.std()) / (
            upper_tolerance - lower_tolerance
    )


def cpk(distribution: Union[AnyDistribution, rv_continuous, np.ndarray], lower_tolerance: float,
        upper_tolerance: float):
    mean = distribution.mean()
    std = distribution.std()
    return min((upper_tolerance - mean), (mean - lower_tolerance)) / (3 * std)


def bins_center(bins: np.ndarray) -> np.ndarray:
    """
    Centers the bin edges of a histogram.

    Parameters
    ----------
    bins
        bin edges.

    Returns
    -------
    np.ndarray
        centered bins.
    """
    return (bins[:-1] + bins[1:]) / 2


def bins_boundaries(bins: np.ndarray) -> np.ndarray:
    """
    Converts bin centers to bin boundaries.

    Parameters
    ----------
    bins
        bin centers.

    Returns
    -------
    np.ndarray
        bin edges.
    """
    width = bins[1] - bins[0]
    return np.concatenate([bins - width / 2, [bins[-1] + width / 2]])


def histogram(values: np.ndarray, bins: int, boundary: Tuple[float, float]) -> Histogram:
    """
    Creates a histogram from the given values.
    The outer classes will also contain all values that are less than or greater than the supplied range.

    Parameters
    ----------
    values
        array from which the histogram should be created from.
    bins
        number of bins.
    boundary
        boundary of the histogram.

    Returns
    -------
    x,y
        bin boundaries and relative histogram frequencies.
    """
    y, x = np.histogram(values, bins, boundary)

    y[0] += (values < boundary[0]).sum()
    y[-1] += (values > boundary[1]).sum()
    return x, y / len(values)


def histedges_equalN(x: np.ndarray, nbin: int) -> np.ndarray:
    """
    Calculates the histogram edges such that every bin has equal amounts of entries.

    See https://stackoverflow.com/a/39419049

    Parameters
    ----------
    x
        values.
    nbin
        number of bins.

    Returns
    -------
    np.ndarray
        histogram bin edges.
    """
    npt = len(x)
    return np.interp(np.linspace(0, npt, nbin + 1), np.arange(npt), np.sort(x))
