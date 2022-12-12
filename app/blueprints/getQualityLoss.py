import json
import os
from typing import List, Optional

import numpy as np
import pandas as pd
from flask import (
    Blueprint, request, jsonify
)
from flask import current_app as app
from werkzeug.exceptions import BadRequest

from app.calculations.allocations import allocate_complete
from app.calculations.convolutions import qc_convolution
from app.calculations.qualitylossfunc import calculate_quality_loss_discrete
from app.utils.qc_strategy import QcStrategy
from app.utils.requests import get_tolerances, parse_qc_strategy
from app.utils.standards import get_standard_characteristic_values
from app.utils.types import Histogram
from app.utils.user_data import get_user_data

bp = Blueprint("qualityloss", __name__)


@bp.route("/getQualityLoss", methods=["POST"])
def get_quality_loss():
    """
    For every test point (and the weighted average of all test points), calculate the loss w.r.t the second entry.

    Input
    -----
    JSON array of characteristic values for every component.
    [
        # Component 1
        {
            "name": "Name",

            # The characteristic values of multiple batches, each one consisting
            # of several klts, with the server automatically performing an allocation.
            "batches": [
                # KLTS for Batch 1
                [
                    # Values for KLT 1
                    [
                        "functional characteristic 1": [ Values for functional characteristic 1 ],
                        "functional characteristic 2": [ Values for functional characteristic 2 ],
                        ...
                    ],
                    # Values for KLT 2
                    ...
                ],
                # KLTS for Batch 2
                [
                ...
                ]
            ]
        },
        # Component 2
        {
            "name": "Name",
            "batches": [
                ...
            ]
        },
        ...
    ]


    Returns
    -------
    Quality loss values.

    [
        ...
    ]
    """
    bins = int(request.args.get("bins"))
    current_config = request.args["c"]
    if "qc_strategy" in request.args:
        qc_strategy = request.args.get("qc_strategy", "")
    else:
        qc_strategy = get_user_data(current_config)["qcStrategy"]
    qc = parse_qc_strategy(qc_strategy)

    tolerances = get_tolerances(current_config)
    inefficiency_costs = app.config[current_config]["QualityLoss"]["InefficiencyCosts"]
    target_means = [app.config[current_config]["MeanValues"][test_point] for test_point in
                    app.config[current_config]["TestPoints"]]
    weights = app.config[current_config]["TestPointWeights"]

    components = request.json
    for component in app.config[current_config]["Components"]:
        if component["name"] not in [c["name"] for c in request.json]:
            # add saved component
            file_name = os.path.join(app.instance_path, "saved_data", current_config, component["name"] + ".json")
            if not os.path.isfile(file_name):
                raise BadRequest("missing component data " + component["name"])
            with open(file_name, "r") as f:
                batches = json.load(f)
            components.append({
                "name": component["name"],
                "batches": batches
            })

    # parse distributions from request
    convolution_histograms = []
    settings_dict = {
        "config": current_config,
        "bins": bins,
        "component_names": [component["name"] for component in components],
        "batch_size": next((len(list(component["batches"][0][0].values())[0]) for component in components if
                            isinstance(component["batches"], list))),
        "klt_number": next(
            (len(component["batches"][0]) for component in components if isinstance(component["batches"], list))),
        "batch_number": next(
            (len(component["batches"]) for component in components if isinstance(component["batches"], list)))
    }

    # parse batches
    components_batches = []
    for component in components:
        if component["batches"] == "standard":
            # sample standard klts
            # this uses the .csv files in the root directory and samples the correct amount of batches
            # alternatively to sampling, the file could be used "as is" like the following:
            # components_batches.append(current_config, get_standard_characteristic_values_batches(component["name"]))
            batches = []
            for batch in range(settings_dict["batch_number"]):
                klts = []
                for klt in range(settings_dict["klt_number"]):
                    seed = (batch + 1) * settings_dict["klt_number"] + (klt + 1)
                    klts.append(
                        get_standard_characteristic_values(current_config, component["name"],
                                                           settings_dict["batch_size"], seed))
                batches.append(klts)
            components_batches.append(batches)
        elif component["batches"] == "optimal":
            # calculate optimal batch
            batches = []
            for batch in range(settings_dict["batch_number"]):
                klts = []
                for klt in range(settings_dict["klt_number"]):
                    characteristic_values = dict()
                    for other_component in components:
                        if isinstance(other_component["batches"], list):
                            other_values = other_component["batches"][batch][klt]
                            for key, values in other_values.items():
                                tol_center = app.config[current_config]["MeanValues"][key]
                                characteristic_values[key] = [v + (tol_center - v) * 2 for v in values]
                    klts.append(pd.DataFrame(characteristic_values))
                batches.append(klts)
            components_batches.append(batches)
        else:
            components_batches.append(
                [[pd.DataFrame.from_dict(klt) for klt in batch] for batch in component["batches"]])

    # noinspection PyTypeChecker
    optimal_permutation = allocate_complete(components_batches, qc, "cpk", "brute_force", settings_dict)
    for base_batch_idx, (comparison_batch_idx, comparison_klts_idx) in zip(range(len(optimal_permutation)),
                                                                           optimal_permutation):
        base_klts = components_batches[0][base_batch_idx]
        comparison_klts = [components_batches[1][comparison_batch_idx][klt_idx] for klt_idx in comparison_klts_idx]
        # noinspection PyTypeChecker
        convolution_histograms.extend(
            batch_convolution(current_config, [base_klts, comparison_klts], qc, bins, weights))

    convolutions = merge_histograms(convolution_histograms)

    # calculate quality loss
    n_components = settings_dict["batch_size"] * settings_dict["batch_number"] * settings_dict["klt_number"]
    losses = [
        n_components * calculate_quality_loss_discrete(distribution, target_mean, inefficiency_costs,
                                                       bound) for
        distribution, target_mean, bound in zip(convolutions, target_means, tolerances)]

    result = {
        "losses": losses,
        "convolutions": [{"x": x.tolist(), "y": (y * n_components).tolist()} for (y, x) in convolutions]
    }
    if np.isclose(tolerances, get_tolerances(current_config)).all():
        result["loss"] = np.average(losses[:-1], weights=weights)

    return jsonify(result)


def batch_convolution(current_config: str, components: List[List[pd.DataFrame]], qc: Optional[QcStrategy], bins: int,
                      weights: Optional[List[float]]) -> List[List[Histogram]]:
    """
    For a list of batches or klts, calculates the convolution of multiple components
    for a given quality strategy.

    Parameters
    ----------
    current_config
        name of the configuration that should be used for the functional model.
    components
        list of components where every entry contains a list of batches or klts.
        Each batch or klt is a data frame of characteristic values.
    qc
        quality control strategy.
    bins
        number of bins for the resulting histogram.
    weights
        list of weights if the weighted test point should be calculated as well.

    Returns
    -------
    List[List[Histogram]]
        for every batch: for every test point a numpy histogram.
    """
    result = []
    for batch_idx in range(len(components[0])):
        result.append(
            qc_convolution(current_config, [component[batch_idx] for component in components], qc, bins, weights))
    return result


def merge_histograms(batch_histograms: List[List[Histogram]]) -> List[Histogram]:
    """
    Merges several histogram into one by summing up their probabilities.

    Parameters
    ----------
    batch_histograms
        list of histograms that should be merged. Each entry of the list contains a histogram
        for every test point. Histograms are merged on a per-test-point basis.

    Returns
    -------
    List[Histogram]
        for every test point, a merged histogram.
    """
    result = []
    for test_point in range(len(batch_histograms[0])):
        x = batch_histograms[0][test_point][1]
        y_axes = [histogram[test_point][0] for histogram in batch_histograms]
        y = np.array([sum(y_values) for y_values in zip(*y_axes)])
        y /= y.sum()
        result.append((y, x))
    return result
