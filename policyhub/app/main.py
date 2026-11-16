import os

from flask import Flask

from app.extensions import db


def create_app() -> Flask:
    app = Flask(__name__)

    # POLICYHUB_DB_PATH is set per learner when the SQValex backend spawns a
    # dedicated instance (see app/core/policyhub_manager.py) - each learner's
    # policies/claims/quotes stay private to them. Falls back to a single
    # shared file for standalone/manual runs.
    db_path = os.environ.get("POLICYHUB_DB_PATH") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "policyhub.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "policyhub-training-sandbox"

    db.init_app(app)

    from app.routes_api import api_bp
    from app.routes_web import web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        from app.seed import seed_demo_data

        seed_demo_data()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
