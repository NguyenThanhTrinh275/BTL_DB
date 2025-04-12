from flask import Flask
from website.config import Config
from website.auth import auth
from website.views import views

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Đăng ký blueprints
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')
    
    return app