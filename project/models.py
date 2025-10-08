# project/models.py

from . import db
from flask_login import UserMixin
import statistics

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# --- NEW: Many-to-many association table for tags, bound to the 'tags' database ---
media_tags = db.Table('media_tags',
    db.Column('media_id', db.Integer, nullable=False),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), nullable=False),
    info={'bind_key': 'tags'}
)

# --- NEW: Tag model, bound to the 'tags' database ---
class Tag(db.Model):
    __bind_key__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False) # 'cinematic' or 'musical'

class Media(db.Model):
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

    # --- NEW: Property that simulates a relationship to fetch tags from the 'tags' database ---
    @property
    def tags(self):
        # Find all tag_ids associated with this media_id from the association table
        tag_ids_query = db.session.query(media_tags.c.tag_id).filter_by(media_id=self.id)
        tag_ids = [item[0] for item in tag_ids_query.all()]
        
        if not tag_ids:
            return []
        
        # Fetch the actual Tag objects using the collected IDs
        return Tag.query.filter(Tag.id.in_(tag_ids)).all()

    @property
    def overall_score(self):
        return self.official_rating if self.official_rating is not None else 0.0

    @property
    def calculated_average_score(self):
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
        else:
            return None
        return round(statistics.mean(ratings), 1) if ratings else 0.0

class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    season_number = db.Column(db.Integer, nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    episodes = db.relationship('Episode', backref='season', cascade="all, delete-orphan", order_by="Episode.episode_number")

    @property
    def average_score(self):
        ratings = [ep.rating for ep in self.episodes if ep.rating is not None]
        return round(statistics.mean(ratings), 1) if ratings else 0.0

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
