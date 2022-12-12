import os

from flask import Flask

from .utils.config import Config, FileConfig


def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    if app.config["ENV"] == "development":
        app.config['TEMPLATES_AUTO_RELOAD'] = True
    # enable python zip function in html templates
    app.jinja_env.globals.update(zip=zip)

    # load the instance config
    app.config["base"] = FileConfig(os.path.join(app.instance_path, "config_base.json"))
    # load the type specific configs
    for c_type in app.config["base"]["config_types"]:
        app.config[c_type] = FileConfig(os.path.join(app.instance_path, f"config_{c_type}.json"))

    from .blueprints import index, dashboard, getFunction, getConvolution, getAllocation, getAllocationComplete, \
        getQualityLoss, uploadCustomerData
    app.register_blueprint(index.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(getFunction.bp)
    app.register_blueprint(getConvolution.bp)
    app.register_blueprint(getAllocation.bp)
    app.register_blueprint(getAllocationComplete.bp)
    app.register_blueprint(getQualityLoss.bp)
    app.register_blueprint(uploadCustomerData.bp)

    return app
