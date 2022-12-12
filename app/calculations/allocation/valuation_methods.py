##################################################################
# METHODS HOW A DISTRIBUTION IS CONVERTED INTO A NUMERICAL VALUE #
##################################################################
from typing import Any, Dict, Callable

from flask import current_app as app
from scipy.stats import rv_histogram

from app.calculations.functionalmodel import get_function
from app.calculations.math import cpk
from app.calculations.qualitylossfunc import calculate_quality_loss_discrete
from app.utils.requests import get_tolerances
from app.utils.types import Histogram


def apply_mean(distribution: Histogram, test_point: int, settings_dict: Dict[str, Any]):
    # when mean != 0 (ie non-relative functional fulfillment), offset value by mean
    means = app.config[settings_dict["config"]]["MeanValues"]
    test_point = app.config[settings_dict["config"]]["TestPoints"][test_point]
    return abs(rv_histogram(distribution).mean() - means[test_point])


def apply_mean_std(distribution: Histogram, test_point: int, settings_dict: Dict[str, Any]):
    # when mean != 0 (ie non-relative functional fulfillment), offset value by mean
    means = app.config[settings_dict["config"]]["MeanValues"]
    test_point = app.config[settings_dict["config"]]["TestPoints"][test_point]

    hist = rv_histogram(distribution)
    return abs(hist.mean() - means[test_point] + hist.std())


def apply_cpk(distribution: Histogram, test_point: int, settings_dict: Dict[str, Any]):
    return -cpk(rv_histogram(distribution), *get_tolerances(settings_dict["config"])[test_point])


_standard_convolutions_cache = {}


def apply_quality_loss(distribution: Histogram, test_point: int, settings_dict: Dict[str, Any]):
    current_config = settings_dict["config"]
    inefficiency_costs = app.config[current_config]["QualityLoss"]["InefficiencyCosts"]

    tolerances = get_tolerances(current_config)
    component_names = settings_dict["component_names"]
    characteristic_values = {}
    for component in component_names:
        characteristics = next((
            x["characteristics"] for x in app.config[current_config]["Components"] if x["name"] == component))
        means = app.config[current_config]["MeanValues"]
        for characteristic in characteristics:
            characteristic_values[characteristic] = means[characteristic]

    convolution_means = get_function(characteristic_values, current_config, weighted=False)
    convolution_mean = convolution_means[test_point]
    batch_size = settings_dict["batch_size"]
    return batch_size * calculate_quality_loss_discrete(distribution, convolution_mean, inefficiency_costs,
                                                        tolerances[test_point])


ValuationMethod = Callable[[Histogram, int, Dict[str, Any]], float]

supported_valuation_methods: Dict[str, ValuationMethod] = {
    "mean": apply_mean,
    "mean_std": apply_mean_std,
    "cpk": apply_cpk,
    "qualityloss": apply_quality_loss,
}
