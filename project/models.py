# project/models.py

from . import db
from flask_login import UserMixin

# Association table for many-to-many between Media and Tags
media_tags = db.Table(
    'media_tags',
    db.Column('media_id', db.Integer, db.ForeignKey('media.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    creator = db.Column(db.String(200))
    years = db.Column(db.String(50))
    media_type = db.Column(db.String(50))
    official_rating = db.Column(db.Float)
    poster_img = db.Column(db.String(200))
    banner_img = db.Column(db.String(200))

    # Relationships
    tracks = db.relationship('Track', backref='media', cascade="all, delete-orphan")
    seasons = db.relationship('Season', backref='media', cascade="all, delete-orphan")
    tags = db.relationship('Tag', secondary=media_tags, back_populates='media_items')

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    track_number = db.Column(db.Integer)
    rating = db.Column(db.Float)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))

class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    season_number = db.Column(db.Integer)
    rating = db.Column(db.Float)
    year = db.Column(db.String(50))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    episodes = db.relationship('Episode', backref='season', cascade="all, delete-orphan")

class Episode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    episode_number = db.Column(db.Integer)
    title = db.Column(db.String(200))
    rating = db.Column(db.Float)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # 'cinematic' or 'musical'

    # Relationship back to Media
    media_items = db.relationship('Media', secondary=media_tags, back_populates='tags')
