import pandas as pd
from flask import (
    Blueprint, request, jsonify
)

from app.calculations.allocation.valuation_methods import supported_valuation_methods
from app.calculations.convolutions import convolve_with_boundary, qc_convolution
from app.utils.requests import parse_distribution, parse_qc_strategy

bp = Blueprint("convolute", __name__)


@bp.route("/getConvolution", methods=["POST"])
def get_convolution():
    """
    Calculates the convolution of two or more distributions.
    All distributions must be centered around zero.

    Input
    -----
    JSON array of distributions.

    {
        "distributions": [
            { distribution 1 },
            { distribution 2 },
            ...
        ],
        "result_histogram": <result_histogram>
    }

    Output
    ------
    JSON dictionary.
    The entry represents the convolution of the functional fulfillment of all components.

    {
        x: [
            # Functional fulfillment axis
        ],
        y: [
            # Functional fulfillment values
        ]
    }
    """

    distributions = request.json["distributions"]
    result_histogram = request.json["result_histogram"]
    bins = result_histogram["bins"]
    boundary = result_histogram["range"]

    # parse distributions from request
    distributions = [parse_distribution(dic) for dic in distributions]
    # convolution of all distributions
    y, x = convolve_with_boundary(distributions, boundary, bins)

    return jsonify({"x": x.tolist(), "y": y.tolist()})


@bp.route("/simulateAssembly", methods=["POST"])
def get_simulate_assembly():
    """
    Calculates the convolution of two or more empirical distributions

    Input
    -----
    JSON array of characteristic values for every component.
    [
        # Component 1
        {
            "name": "Name",
            "characteristics": [
                "functional characteristic 1": [ Values for functional characteristic 1 ],
                "functional characteristic 2": [ Values for functional characteristic 2 ],
                ...
            ]
        },
        # Component 2
        {
            "name": "Name",
            "characteristics": [
                ...
            ]
        },
        ...
    ]

    Output
    ------
    JSON array.
    Every element of the array represents one test point. For every test point the entry
    represents the convolution of the functional fulfillment of all components.

    [
        # Test Point 1
        [
            # Functional fulfillment values
        ],
        # Test Point 2
        [
            ...
        ],
        ...
    ]
    """
    component_names = [component["name"] for component in request.json]
    components = request.json
    for componentIdx in range(len(components)):
        components[componentIdx] = pd.DataFrame.from_dict(components[componentIdx]["characteristics"])

    qc_strategy = request.args.get("qc_strategy", "")
    qc = parse_qc_strategy(qc_strategy)
    bins = int(request.args.get("bins"))

    current_config = request.args["c"]

    # noinspection PyTypeChecker
    convolutions = qc_convolution(current_config, components, qc, bins, None)
    result = []
    settings_dict = {
        "config": current_config,
        "batch_size": len(components[0]),
        "component_names": component_names,
        "bins": bins
    }
    for test_point, histogram in enumerate(convolutions):
        dic = {
            "x": histogram[1].tolist(),
            "y": histogram[0].tolist(),
        }
        for name, valuation_method in supported_valuation_methods.items():
            dic[name] = valuation_method(histogram, test_point, settings_dict)
        result.append(dic)

    return jsonify(result)
