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
    # Ensure the instance folder exists. Flask will create it.
    os.makedirs(app.instance_path, exist_ok=True)
    
    # **FIXED LINE:** Correctly set the database path inside the instance folder
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'media_rater.db')}"
    
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    
    # Ensure upload folder exists (instance folder is handled above)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    # --- Login Manager ---
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Blueprints (Routes) ---
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # --- Create Database and Admin User ---
    with app.app_context():
        db.create_all()
        # Create Admin User if not exists
        if not User.query.filter_by(username='Ryan').first():
            hashed_password = generate_password_hash('06242005', method='pbkdf2:sha256')
            admin_user = User(username='Ryan', password=hashed_password)
            db.session.add(admin_user)
            db.session.commit()

    return app
