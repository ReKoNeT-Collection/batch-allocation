import pandas as pd
from flask import (
    Blueprint, request, jsonify
)

from app.calculations import functionalmodel

bp = Blueprint("functionalmodel", __name__)


@bp.route("/getFunction", methods=["POST"])
def get_function():
    """
    Calculates the functional fulfillment for the given characteristic values.

    Input
    -----
    JSON dictionary with different functional characteristic values.
    {
        "functional characteristic 1": [ Values for functional characteristic 1 ],
        "functional characteristic 2": [ Values for functional characteristic 2 ],
        ...
    }

    Output
    ------
    JSON array with one entry per test point and one weighted entry.
    [
        [ Values for test point 1 ],
        ...
        [ Values for test point m ],
        [ Weighted values for all test points ]
    ]
    """

    # config values
    current_config = request.args["c"]

    # create a data frame from the contents of the json request
    characteristic_values = pd.DataFrame.from_dict(request.json)

    # calculate functional fulfillment
    result = functionalmodel.get_batch_function(characteristic_values, current_config, True)

    # transform the pandas data frame into a dict
    result_dict = result.to_dict(orient="list")
    # result is [[<values for point 1>], ..., [<values for point m>]]
    return jsonify([v for _, v in result_dict.items()])
