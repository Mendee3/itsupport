from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import inspect, text
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "oncall.db")
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "admin.login"


def resolve_database_uri():
    uri = os.environ.get("DATABASE_URL", "").strip()
    if not uri:
        return f"sqlite:///{DB_PATH}"

    # Some platforms expose postgres:// which SQLAlchemy 2 rejects.
    if uri.startswith("postgres://"):
        return "postgresql://" + uri[len("postgres://"):]

    return uri


def ensure_engineer_columns():
    inspector = inspect(db.engine)
    if "engineer" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("engineer")}
    missing = []

    if "position" not in existing:
        missing.append("ALTER TABLE engineer ADD COLUMN position VARCHAR(120)")
    if "shift_start" not in existing:
        missing.append("ALTER TABLE engineer ADD COLUMN shift_start VARCHAR(20)")
    if "shift_end" not in existing:
        missing.append("ALTER TABLE engineer ADD COLUMN shift_end VARCHAR(20)")
    if "responsibilities" not in existing:
        missing.append("ALTER TABLE engineer ADD COLUMN responsibilities VARCHAR(255)")

    if not missing:
        return

    for statement in missing:
        db.session.execute(text(statement))
    db.session.commit()

def create_app():
    from werkzeug.middleware.proxy_fix import ProxyFix
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "CHANGE_ME_TO_RANDOM_LONG_STRING"
    app.config["SQLALCHEMY_DATABASE_URI"] = resolve_database_uri()
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
        ensure_engineer_columns()

    return app
