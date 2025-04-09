from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Khởi tạo database
    db.init_app(app)

    # Import và đăng ký các blueprint
    from . import auth, views
    app.register_blueprint(auth.bp)
    app.register_blueprint(views.bp)

    return app