# project/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FileField, IntegerField, FloatField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class EpisodeForm(FlaskForm):
    episode_number = IntegerField('E#', validators=[DataRequired()])
    title = StringField('Title')
    rating = FloatField('Rating', validators=[Optional(), NumberRange(min=0, max=10)])

class SeasonForm(FlaskForm):
    season_number = IntegerField('S#', validators=[DataRequired()])
    episodes = FieldList(FormField(EpisodeForm))

class TrackForm(FlaskForm):
    track_number = IntegerField('T#', validators=[DataRequired()])
    title = StringField('Title')
    rating = FloatField('Rating', validators=[Optional(), NumberRange(min=0, max=10)])

class MediaForm(FlaskForm):
    media_type = SelectField('Type', choices=[
        ('tv_show', 'TV Show'),
        ('album', 'Album'),
        ('movie', 'Movie'),
        ('single', 'Single')
    ], validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    creator = StringField('Creator/Artist')
    years = StringField('Years (e.g., 2015-2019)')
    poster_img = FileField('Poster Image')
    banner_img = FileField('Banner Image')
    
    # UPDATED: This field is now for all media types
    official_rating = FloatField('Official Rating', validators=[Optional(), NumberRange(min=0, max=10)])
    
    # Dynamic fields for seasons/tracks will be handled in the route
    submit = SubmitField('Save Media')
