from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from dotenv import load_dotenv
load_dotenv()
from config import DevelopmentConfig, ProductionConfig

config = DevelopmentConfig if os.getenv('FLASK_ENV') == 'development' else ProductionConfig

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, QRCode

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(user=current_user)

    return app