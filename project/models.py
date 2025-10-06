# project/models.py

from . import db
from flask_login import UserMixin
import statistics

class User(UserMixin, db.Model):
    # This model uses the default database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class TitleStyle(db.Model):
    # --- NEW: This model will live in the 'colors' database ---
    __bind_key__ = 'colors'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), nullable=False)
    token_index = db.Column(db.Integer, nullable=False)
    color1 = db.Column(db.String(7), nullable=False, default='#FFFFFF')
    color2 = db.Column(db.String(7), nullable=True)
    media_id = db.Column(db.Integer, nullable=False) # This is just an ID, not a formal foreign key

    # Helper function to make passing data to Jinja easier
    def to_dict(self):
        return {
            'token': self.token,
            'token_index': self.token_index,
            'color1': self.color1,
            'color2': self.color2
        }

class Media(db.Model):
    # This model uses the default database
    id = db.Column(db.Integer, primary_key=True)
    media_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    creator = db.Column(db.String(150), nullable=True)
    years = db.Column(db.String(50))
    poster_img = db.Column(db.String(200))
    banner_img = db.Column(db.String(200))
    
    seasons = db.relationship('Season', backref='media', cascade="all, delete-orphan")
    tracks = db.relationship('Track', backref='media', cascade="all, delete-orphan")
    
    official_rating = db.Column(db.Float)

    # --- NEW: A property that manually fetches styles from the other database ---
    # This perfectly mimics a relationship for the templates.
    @property
    def title_styles(self):
        return TitleStyle.query.filter_by(media_id=self.id).order_by(TitleStyle.token_index).all()

    @property
    def overall_score(self):
        # ... same as before ...
    # ... other properties ...

# ... Season, Episode, and Track models remain unchanged ...
