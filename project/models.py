# project/models.py

from . import db
from flask_login import UserMixin
import statistics

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    media_type = db.Column(db.String(50), nullable=False) # 'tv_show', 'album', 'movie', 'single'
    title = db.Column(db.String(200), nullable=False)
    years = db.Column(db.String(50))
    poster_img = db.Column(db.String(200))
    banner_img = db.Column(db.String(200))
    
    # Relationships
    seasons = db.relationship('Season', backref='media', cascade="all, delete-orphan")
    tracks = db.relationship('Track', backref='media', cascade="all, delete-orphan")
    
    # For movies and singles
    single_rating = db.Column(db.Float)

    @property
    def overall_score(self):
        ratings = []
        if self.media_type == 'tv_show':
            for season in self.seasons:
                for episode in season.episodes:
                    if episode.rating is not None:
                        ratings.append(episode.rating)
        elif self.media_type == 'album':
            for track in self.tracks:
                if track.rating is not None:
                    ratings.append(track.rating)
        elif self.media_type in ['movie', 'single']:
            return self.single_rating if self.single_rating else 0.0

        if not ratings:
            return 0.0
        return round(statistics.mean(ratings), 1)

class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    season_number = db.Column(db.Integer, nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    episodes = db.relationship('Episode', backref='season', cascade="all, delete-orphan", order_by="Episode.episode_number")

class Episode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    episode_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    rating = db.Column(db.Float)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    track_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    rating = db.Column(db.Float)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
