from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "oncall.db")
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "admin.login"

def create_app():
    from werkzeug.middleware.proxy_fix import ProxyFix
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "CHANGE_ME_TO_RANDOM_LONG_STRING"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)

    from .routes_public import public_bp
    from .routes_admin import admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        from . import models  # noqa
        db.create_all()

    return app
