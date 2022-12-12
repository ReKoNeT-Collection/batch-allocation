import json
import os.path

from flask import (
    Blueprint, request
)
from flask import current_app as app
from werkzeug.exceptions import BadRequest

from app.utils.user_data import get_user_data, save_user_data

bp = Blueprint("customerdata", __name__)


@bp.route("/uploadCustomerData/<data_type>", methods=["POST"])
def get_function(data_type):
    """
    Calculates the functional fulfillment for the given characteristic values.

    Input
    -----


    Output
    ------
    {"status": "Erfolgreich hochgeladen"}
    """
    # config values
    current_config = request.args["c"]
    data = request.json

    if data_type == "componentData":
        for component, data in data.items():
            dir_name = os.path.join(app.instance_path, "saved_data", current_config)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            file_name = os.path.join(dir_name, component + ".json")
            with open(file_name, "w") as f:
                json.dump(data, f)
    elif data_type == "qcStrategy":
        settings = get_user_data(current_config)
        settings["qcStrategy"] = data
        save_user_data(current_config, settings)
    else:
        raise BadRequest()

    return {"status": "Erfolgreich hochgeladen"}, 200
