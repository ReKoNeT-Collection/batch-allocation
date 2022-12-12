import pandas as pd
from flask import Blueprint, request, jsonify

from app.calculations.allocations import allocate
from app.utils.requests import parse_qc_strategy

bp = Blueprint("allocate", __name__)


@bp.route("/getAllocation", methods=["POST"])
def get_allocation():
    """
    Tries to find the best allocation of batches of two or more components.

    Input
    -----
    JSON array of characteristic values for every component.

    [
        {
            # Name of component 1
            "name": "Modul1",
            "batches": [
                # Batch 1
                [
                    "functional characteristic 1": [ Values for functional characteristic 1 ],
                    "functional characteristic 2": [ Values for functional characteristic 2 ],
                    ...
                ]
                # Batch 2
                [
                    ...
                ],
                ...
            ]
        },
        {
            # Name of component 2
            "name": "Modul2",
            "batches": [
                ...
            ]
        }
    ]

    Output
    ------
    The optimal batch allocation.

    Example:
    {
        "permutation": [0, 1, 2],
        "values": [0.35, -0.3, 0]
    }
    """
    ####################################################################
    # READ INPUTS                                                      #
    ####################################################################

    algorithm = request.args.get("algorithm", "brute_force")
    method = request.args.get("method", "mean")
    qc_strategy = request.args.get("qc_strategy", "")
    qc = parse_qc_strategy(qc_strategy)

    bins = int(request.args.get("bins"))
    batch_size = len(list(request.json[0]["batches"][0].values())[0])
    current_config = request.args["c"]

    # parse distributions
    components = []
    for component in request.json:
        batches = []
        for batch in component["batches"]:
            batches.append(pd.DataFrame.from_dict(batch))
        components.append(batches)

    # todo: replace with struct
    settings_dict = {
        "config": current_config,
        "bins": bins,
        "batch_size": batch_size,
        "component_names": [component["name"] for component in request.json],
    }

    # noinspection PyTypeChecker
    optimal_permutation, scalar = allocate(components, qc, method, algorithm, settings_dict)

    return jsonify({"permutation": optimal_permutation, "values": scalar})
