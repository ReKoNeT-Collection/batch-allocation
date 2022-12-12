import pandas as pd
from flask import Blueprint, request, jsonify

from app.calculations.allocations import allocate_complete
from app.utils.requests import parse_qc_strategy

bp = Blueprint("allocate_complete", __name__)


@bp.route("/getAllocationComplete", methods=["POST"])
def get_allocation_complete():
    """
    Tries to find the best allocation of batches of two or more components.

    Input
    -----
    JSON array of characteristic values for every component.
    [
        # Component 1
        {
            "name": "Name",

            # The characteristic values of multiple batches, each one consisting of several klts
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

    Output
    ------
    The optimal batch allocation of the second component.
    First component is assumed to have the initially supplied order.

    Example:
    [
        {
            "batch": 0,
            "klts": [0, 1, 2]
        },
        {
            "batch": 2,
            "klts": [1, 0, 2]
        },
        {
            "batch": 1,
            "klts": [2, 1, 0]
        }
    ]
    """
    ####################################################################
    # READ INPUTS                                                      #
    ####################################################################

    algorithm = request.args.get("algorithm", "brute_force")
    method = request.args.get("method", "mean")
    qc_strategy = request.args.get("qc_strategy", "")
    qc = parse_qc_strategy(qc_strategy)

    bins = int(request.args.get("bins"))
    batch_size = len(list(request.json[0]["batches"][0][0].values())[0])
    current_config = request.args["c"]

    # parse distributions
    components_batches = []
    for component in request.json:
        components_batches.append(
            [[pd.DataFrame.from_dict(klt) for klt in batch] for batch in component["batches"]])

    # todo: replace with struct
    settings_dict = {
        "config": current_config,
        "bins": bins,
        "batch_size": batch_size,
        "component_names": [component["name"] for component in request.json],
    }

    # noinspection PyTypeChecker
    optimal_permutation = allocate_complete(components_batches, qc, method, algorithm, settings_dict)

    return jsonify([{"batch": batch, "klts": klts} for batch, klts in optimal_permutation])
