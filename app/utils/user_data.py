import json
import os

from flask import current_app as app


def get_user_data(config: str) -> dict:
    file_name = os.path.join(app.instance_path, "saved_data", config, "settings.json")
    if not os.path.isfile(file_name):
        return {
            "qcStrategy": ""
        }
    else:
        with open(file_name, "r") as f:
            return json.load(f)


def save_user_data(config: str, data: dict):
    dir_name = os.path.join(app.instance_path, "saved_data", config)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    file_name = os.path.join(dir_name, "settings.json")
    with open(file_name, "w") as f:
        return json.dump(data, f, ensure_ascii=False, indent=2)
