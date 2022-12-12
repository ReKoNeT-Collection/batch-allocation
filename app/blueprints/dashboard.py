import json
import os

import numpy as np
import pandas as pd
from flask import (
    Blueprint, render_template, redirect
)
from flask import current_app as app

from app.calculations.functionalmodel import get_batch_function
from app.calculations.math import bins_center
from app.calculations.qualitylossfunc import calculate_quality_loss
from app.utils.requests import get_tolerances, get_fulfillment_axis_range
from app.utils.standards import get_standard_characteristic_values

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard/<current_config>")
def dashboard(current_config):
    if current_config is None:
        return redirect("/")
    component_names = [component["name"] for component in app.config[current_config]["Components"]]
    return render_template(
        "admin/0_dashboard.html.jinja2",
        components=component_names,
        tolerances=app.config[current_config]["Tolerances"],
        testPointNames=app.config[current_config]["TestPoints"],
        componentsCharacteristics=app.config[current_config]["Components"],
        n_testPoints=len(app.config[current_config]["TestPoints"]) - 1,
        standardDistributions=get_standard_distributions(current_config, component_names),
        qualityLossClasses=get_quality_loss_discrete(current_config),
        currentConfig=current_config,
        currentConfigName=app.config[current_config]["Name"],
        means=app.config[current_config]["MeanValues"]
    )


@bp.route("/customer/<current_config>")
def customer_dashboard(current_config):
    if current_config is None:
        return redirect("/")
    return render_template(
        "customer/0_dashboard.html.jinja2",
        components=app.config[current_config]["Customer"]["Components"],
        tolerances=app.config[current_config]["Tolerances"],
        testPointNames=app.config[current_config]["TestPoints"],
        componentsCharacteristics=app.config[current_config]["Components"],
        n_testPoints=len(app.config[current_config]["TestPoints"]) - 1,
        currentConfig=current_config,
        currentConfigName=app.config[current_config]["Name"],
        standardDistributions=get_standard_distributions(current_config,
                                                         app.config[current_config]["Customer"]["Components"])
    )


@bp.route("/supplier/<current_config>")
def supplier_dashboard(current_config):
    if current_config is None:
        return redirect("/")
    return render_template(
        "supplier/0_dashboard.html.jinja2",
        components=app.config[current_config]["Supplier"]["Components"],
        tolerances=app.config[current_config]["Tolerances"],
        testPointNames=app.config[current_config]["TestPoints"],
        componentsCharacteristics=app.config[current_config]["Components"],
        n_testPoints=len(app.config[current_config]["TestPoints"]) - 1,
        currentConfig=current_config,
        currentConfigName=app.config[current_config]["Name"],
        standardDistributions=get_standard_distributions(current_config,
                                                         app.config[current_config]["Supplier"]["Components"])
    )


def get_quality_loss_discrete(current_config: str):
    tolerances = get_tolerances(current_config)
    bins = app.config[current_config]["Bins"]
    boundaries = get_fulfillment_axis_range(tolerances, bins)
    x_axes = [np.linspace(*bounds, bins) for bounds in boundaries]
    tolerances = get_tolerances(current_config)
    inefficiency_costs = app.config[current_config]["QualityLoss"]["InefficiencyCosts"]
    return [{"x": x_axis.tolist(),
             "y": calculate_quality_loss(bins_center(x_axis), 0, inefficiency_costs, tol).tolist()} for x_axis, tol
            in zip(x_axes, tolerances)]


def get_standard_distributions(current_config: str, component_names):
    histograms = {}
    bins = app.config[current_config]["Bins"]
    tolerances = get_tolerances(current_config)
    boundaries = get_fulfillment_axis_range(tolerances, bins)

    def function_hist_for_characteristic_values(component: str, characteristic_values: pd.DataFrame):
        distributions = get_batch_function(characteristic_values, current_config, True)
        histograms[component] = []
        for test_point in range(len(distributions.columns)):
            histogram = np.histogram(distributions[distributions.columns[test_point]], bins=bins,
                                     range=boundaries[test_point])
            histograms[component].append(
                {"x": histogram[1].tolist(), "y": (histogram[0] / histogram[0].sum()).tolist()})

    # add standard components of supplier
    for component in component_names:
        characteristic_values = get_standard_characteristic_values(current_config, component, None)
        function_hist_for_characteristic_values(component, characteristic_values)

    # add previously uploaded distributions of all other components
    for component in app.config[current_config]["Components"]:
        if component["name"] in component_names:
            continue
        # add saved component
        file_name = os.path.join(app.instance_path, "saved_data", current_config, component["name"] + ".json")
        if not os.path.isfile(file_name):
            continue
        with open(file_name, "r") as f:
            batches = json.load(f)

        characteristic_values = pd.concat([pd.DataFrame(y) for x in batches for y in x], axis=0).reset_index()
        function_hist_for_characteristic_values(component["name"], characteristic_values)

    return histograms
