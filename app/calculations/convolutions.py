from itertools import product
from typing import Tuple, List, Optional

import numpy as np
import pandas as pd
from scipy.signal import convolve
from scipy.stats import rv_continuous

from app.calculations.functionalmodel import get_batch_function
from app.calculations.math import bins_boundaries
from app.calculations.simulation import simulate_assembly
from app.utils.qc_strategy import QcStrategy
from app.utils.requests import get_tolerances, get_fulfillment_axis_range, parse_array_as_hist
from app.utils.types import Histogram


def convolution(distributions):
    """
    Calculates the cartesian product from all distributions.

    Parameters
    ----------
    distributions
        list of distributions

    Returns
    -------
    list
        the convolution
    """
    # https://stackoverflow.com/a/46744050/14094743
    cartesian_product_index = pd.MultiIndex.from_product(distributions)
    cartesian_product_df = pd.DataFrame(index=cartesian_product_index).reset_index(drop=True)
    # Calculate the sum of each row
    conv = cartesian_product_df.sum(axis=1).tolist()
    return conv


def convolution2d(histograms):
    """
    Calculates the cartesian product from all histograms.

    Parameters
    ----------
    histograms
        list of histograms (with x and y values)

    Returns
    -------
    dict
        the convolution
    """
    convolution = histograms.pop(0)
    for histogram in histograms:
        x_prod = product(convolution["x"], histogram["x"])
        y_prod = product(convolution["y"], histogram["y"])
        df = pd.DataFrame((x + y for x, y in zip(x_prod, y_prod)))
        df[4] = df[0] + df[1]
        df[5] = df[2] * df[3]
        df = df[[4, 5]].groupby(4).sum().reset_index()
        convolution = {"x": df[4].values, "y": df[5].values}
    return convolution


def pdf_with_boundary(distribution: rv_continuous, grid: np.ndarray) -> np.ndarray:
    """
    Calculates the discrete probability function for a grid.

    If the sum of the pdf does not add up to 1,
    this method adds the remaining probability to both the left and right side.

    Parameters
    ----------
    distribution
        distribution for which the pdf should be calculated for.
    grid
        discrete grid.

    Returns
    -------
    np.ndarray
        probability distribution inside the discrete grid.
    """
    delta = grid[1] - grid[0]
    pdf = distribution.pdf(grid) * delta

    pdf_sum = pdf.sum()
    outer = (1 - pdf_sum) / 2
    if pdf_sum < 1:
        # if sum of pdf does not add up to 1, add the remaining probability to both the left and right side
        pdf[0] += outer
        pdf[-1] += outer
    elif pdf_sum > 1:
        # if sum of pdfs is slightly greater than 1, normalize the pdf
        pdf /= pdf_sum

    return pdf


def convolve_with_boundary(distributions: List[rv_continuous], boundary: Tuple[float, float], bins: int) -> Histogram:
    """
    Convolves multiple continuous distributions by discretizing them into a grid,
    specified by the given boundary and bin number.
    The distributions have to be centered around zero, as the x-axis is always centered around this value.

    If a distribution has values outside the given boundary,
    then this probability is added to both the left and right side.

    The result is a histogram with the given boundaries, where all probability outside
    the boundary is added to the outer classes respectively.

    Parameters
    ----------
    distributions
        list of probability distributions.
    boundary
        lower and upper boundary.
    bins
        number of bins, which determines both the grid size and returned histogram.

    Returns
    -------
    Histogram
        y and x axis of the histogram.

    """
    # create a discrete grid from the boundaries
    # note that we need to convert to class centers
    delta = (boundary[1] - boundary[0]) / bins
    boundary_center = (boundary[0] + delta / 2, boundary[1] - delta / 2)
    grid = np.arange(boundary_center[0], boundary_center[1], delta)
    if boundary_center[1] - grid[-1] > delta / 2:
        grid = np.concatenate([grid, np.array([boundary_center[1]])])
    assert len(grid) == bins

    # calculate probability densities for the discrete grid
    pdfs = [pdf_with_boundary(dist, grid) for dist in distributions]

    # convolution
    conv_pdf = pdfs.pop(0)
    for pdf in pdfs:
        conv_pdf = convolve(conv_pdf, pdf, mode="full")

        # sum up everything outside the original boundary and add the result to the border classes
        clamp_index = int(np.ceil((len(grid) + 1) / 2))
        conv_pdf = np.concatenate([np.array([conv_pdf[:clamp_index].sum()]), conv_pdf[clamp_index:-clamp_index],
                                   np.array([conv_pdf[-clamp_index:].sum()])])

    if len(grid) % 2 == 1:
        return conv_pdf, bins_boundaries(grid)
    else:
        return conv_pdf, grid


def qc_convolution(current_config: str, distributions: List[pd.DataFrame], qc: Optional[QcStrategy], bins: int,
                   weights: Optional[List[float]]) -> List[Histogram]:
    """
    Calculates the convolution of multiple distributions for a given quality strategy.

    Parameters
    ----------
    current_config
        name of the configuration that should be used for the functional model.
    distributions
        characteristic values for each component.
    qc
        quality control strategy.
    bins
        number of bins for the resulting histogram.
    weights
        list of weights if the weighted test point should be calculated as well.

    Returns
    -------
    List[Histogram]
        for every test point, a numpy histogram.
    """
    tolerances = get_tolerances(current_config)
    boundaries = get_fulfillment_axis_range(tolerances, bins)

    convolutions = []
    if qc is None:
        fulfillments = [get_batch_function(component, current_config) for component in distributions]

        if weights:
            # weighted test point
            for fulfillment in fulfillments:
                fulfillment[len(fulfillment.columns)] = np.average(fulfillment, weights=weights, axis=1)

        # do a statistical convolution
        for test_point in range(len(fulfillments[0].columns)):
            distributions = [
                parse_array_as_hist(fulfillment[fulfillment.columns[test_point]], bins, boundaries[test_point])
                for fulfillment in fulfillments]
            # convolution of all distributions
            convolutions.append(convolve_with_boundary(distributions, boundaries[test_point], bins))
    else:
        # simulate the quality control strategy
        # noinspection PyTypeChecker
        distributions, _ = simulate_assembly(qc, distributions[0], distributions[1], current_config)
        # create histograms for every test point
        for test_point in range(len(distributions.columns)):
            histogram = np.histogram(distributions[distributions.columns[test_point]], bins=bins,
                                     range=boundaries[test_point])
            convolutions.append(((histogram[0] / histogram[0].sum()), histogram[1]))

        if weights:
            # create histogram for weighted test point
            histogram = np.histogram(np.average(distributions, weights=weights, axis=1), bins=bins,
                                     range=boundaries[len(weights)])
            convolutions.append(((histogram[0] / histogram[0].sum()), histogram[1]))

    return convolutions
