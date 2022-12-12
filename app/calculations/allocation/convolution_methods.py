##################################################################
# METHODS HOW TWO DISTRIBUTIONS ARE CONVOLUTED                   #
##################################################################
from typing import List, Dict, Any, Callable, Optional

import numpy as np
import pandas as pd

from app.calculations.convolutions import convolve_with_boundary
from app.calculations.functionalmodel import get_batch_function
from app.calculations.simulation import simulate_assembly
from app.utils.qc_strategy import QcStrategy
from app.utils.requests import parse_array_as_hist, get_fulfillment_axis_range, get_tolerances
from app.utils.types import Histogram


def default_convolution(batches_a: pd.DataFrame, batches_b: pd.DataFrame,
                        settings_dict: Dict[str, Any]) -> List[Histogram]:
    bins = settings_dict["bins"]
    tolerances = get_tolerances(settings_dict["config"])
    axis_range = get_fulfillment_axis_range(tolerances, bins)

    functions_a = get_batch_function(batches_a, settings_dict["config"])
    functions_b = get_batch_function(batches_b, settings_dict["config"])
    distributions_a = [parse_array_as_hist(functions_a[functions_a.columns[test_point]], bins, axis_range[test_point])
                       for test_point in range(len(functions_a.columns))]
    distributions_b = [parse_array_as_hist(functions_b[functions_b.columns[test_point]], bins, axis_range[test_point])
                       for test_point in range(len(functions_b.columns))]
    return [convolve_with_boundary([a, b], boundary, bins) for a, b, boundary in
            zip(distributions_a, distributions_b, axis_range)]


def simulation_convolution(qc_strategy: QcStrategy, batches_a: pd.DataFrame, batches_b: pd.DataFrame,
                           settings_dict: Dict[str, Any]) -> List[Histogram]:
    result, _ = simulate_assembly(qc_strategy, batches_a, batches_b, settings_dict["config"])
    distributions = np.transpose(np.array(result), (1, 0))

    bins = settings_dict["bins"]
    tolerances = get_tolerances(settings_dict["config"])
    axis_range = get_fulfillment_axis_range(tolerances, bins)
    return [np.histogram(distribution, bins, boundary, density=True) for distribution, boundary in
            zip(distributions, axis_range)]


def simulate_selective(batches_a: pd.DataFrame, batches_b: pd.DataFrame,
                       settings_dict: Dict[str, Any]) -> List[Histogram]:
    return simulation_convolution(QcStrategy.selective_assembly, batches_a, batches_b, settings_dict)


def simulate_individual(batches_a: pd.DataFrame, batches_b: pd.DataFrame,
                        settings_dict: Dict[str, Any]) -> List[Histogram]:
    return simulation_convolution(QcStrategy.individual_assembly, batches_a, batches_b, settings_dict)


def simulate_individual_greedy(batches_a: pd.DataFrame, batches_b: pd.DataFrame,
                               settings_dict: Dict[str, Any]) -> List[Histogram]:
    return simulation_convolution(QcStrategy.individual_assembly_greedy, batches_a, batches_b, settings_dict)


def simulate_ascending_descending(batches_a: pd.DataFrame, batches_b: pd.DataFrame,
                                  settings_dict: Dict[str, Any]) -> List[Histogram]:
    return simulation_convolution(QcStrategy.ascending_descending, batches_a, batches_b, settings_dict)


def simulate_ascending_descending_grouped(batches_a: pd.DataFrame, batches_b: pd.DataFrame,
                                          settings_dict: Dict[str, Any]) -> List[Histogram]:
    return simulation_convolution(QcStrategy.ascending_descending_grouped, batches_a, batches_b, settings_dict)


ConvolutionMethod = Callable[[pd.DataFrame, pd.DataFrame, Dict[str, Any]], List[Histogram]]

supported_convolution_methods: Dict[Optional[QcStrategy], ConvolutionMethod] = {
    None: default_convolution,
    QcStrategy.selective_assembly: simulate_selective,
    QcStrategy.individual_assembly: simulate_individual,
    QcStrategy.individual_assembly_greedy: simulate_individual_greedy,
    QcStrategy.ascending_descending: simulate_ascending_descending,
    QcStrategy.ascending_descending_grouped: simulate_ascending_descending_grouped,
}
