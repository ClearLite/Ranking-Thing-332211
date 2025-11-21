# project/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

# --- NEW: Enable SQLite Foreign Key Constraints ---
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    app.config['SECRET_KEY'] = 'a_very_secret_key_change_this'
    os.makedirs(app.app_context().app.instance_path, exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'media_rater.db')}"
    
    app.config['SQLALCHEMY_BINDS'] = {
        'tags': f"sqlite:///{os.path.join(app.instance_path, 'tags.db')}"
    }
    
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    # --- Login Manager ---
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    from . import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # --- Blueprints (Routes) ---
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # --- Create Databases and Initial Data ---
    with app.app_context():
        db.create_all()
        
        def populate_tags():
            cinematic_tags = [
                'Action', 'Adventure', 'Comedy', 'Drama', 'Romance', 'Horror',
                'Thriller / Suspense', 'Science Fiction (Sci-Fi)', 'Fantasy',
                'Crime / Mystery', 'Documentary', 'Animation', 'Anime', 'Marvel'
            ]
            
            musical_tags = [
                'Pop', 'Rock', 'Hip-Hop / Rap', 'R&B / Soul', 'Country', 'Jazz',
                'Classical', 'EDM', 'Reggae', 'Metal', 'Folk', 'Blues'
            ]

            for tag_name in cinematic_tags:
                if not models.Tag.query.filter_by(name=tag_name, category='cinematic').first():
                    new_tag = models.Tag(name=tag_name, category='cinematic')
                    db.session.add(new_tag)
            
            for tag_name in musical_tags:
                if not models.Tag.query.filter_by(name=tag_name, category='musical').first():
                    new_tag = models.Tag(name=tag_name, category='musical')
                    db.session.add(new_tag)
            
            db.session.commit()
        
        populate_tags()

        if not models.User.query.filter_by(username='Ryan').first():
            hashed_password = generate_password_hash('06242005', method='pbkdf2:sha256')
            admin_user = models.User(username='Ryan', password=hashed_password)
            db.session.add(admin_user)
            db.session.commit()

    return app
