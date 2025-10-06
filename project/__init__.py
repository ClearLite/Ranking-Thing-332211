# project/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    app.config['SECRET_KEY'] = 'a_very_secret_key_change_this'
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Define the primary (default) database
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'media_rater.db')}"
    
    # --- NEW: Define the second database for title styles ---
    app.config['SQLALCHEMY_BINDS'] = {
        'colors': f"sqlite:///{os.path.join(app.instance_path, 'title_styles.db')}"
    }
    
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    # --- Login Manager ---
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    # Import models here so they are registered with the db instance
    from . import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # --- Blueprints (Routes) ---
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # --- Create Databases and Admin User ---
    with app.app_context():
        # Flask-SQLAlchemy is smart enough to create all tables in their respective databases
        db.create_all() 
        
        # This logic only touches the default (media_rater.db) database
        if not models.User.query.filter_by(username='Ryan').first():
            hashed_password = generate_password_hash('06242005', method='pbkdf2:sha256')
            admin_user = models.User(username='Ryan', password=hashed_password)
            db.session.add(admin_user)
            db.session.commit()

    return app
