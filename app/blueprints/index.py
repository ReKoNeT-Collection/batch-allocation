from flask import (
    Blueprint, render_template
)
from flask import current_app as app

bp = Blueprint("index", __name__)


@bp.route("/")
def index():
    config_types = app.config["base"]["config_types"]
    config_names = [app.config[c_type]["Name"] for c_type in config_types]
    return render_template(
        "index.html.jinja2",
        config_types=config_types,
        config_names=config_names,
    )

