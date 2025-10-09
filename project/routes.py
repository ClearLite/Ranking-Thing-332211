# project/routes.py

import os
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from . import db
from .models import User, Media, Season, Episode, Track, Tag, media_tags
from .forms import LoginForm, MediaForm

main = Blueprint('main', __name__)

def get_rating_class(rating):
    if rating is None: return "garbage"
    if rating >= 9.0: return "awesome"
    if rating >= 8.0: return "great"
    if rating >= 7.0: return "good"
    if rating >= 6.0: return "okay"
    if rating >= 5.0: return "bad"
    return "garbage"

@main.route('/')
def index():
    sort_by = request.args.get('sort', 'title_asc')
    filter_type = request.args.get('filter', 'all')
    tag_filter = request.args.get('tag', 'all')

    query = Media.query

    if filter_type != 'all':
        query = query.filter(Media.media_type == filter_type)

    if tag_filter != 'all':
        try:
            tag_id = int(tag_filter)
            media_ids_with_tag = db.session.query(media_tags.c.media_id).filter_by(tag_id=tag_id)
            query = query.filter(Media.id.in_([item[0] for item in media_ids_with_tag]))
        except (ValueError, TypeError):
            pass
    
    all_media_list = query.all()

    def get_year_for_sort(media_item):
        if not media_item.years:
            return 0
        try:
            return int(media_item.years[:4])
        except (ValueError, IndexError):
            return 0

    if sort_by == 'score_desc':
        all_media_list.sort(key=lambda m: m.overall_score, reverse=True)
    elif sort_by == 'score_asc':
        all_media_list.sort(key=lambda m: m.overall_score)
    elif sort_by == 'year_desc':
        all_media_list.sort(key=get_year_for_sort, reverse=True)
    elif sort_by == 'year_asc':
        all_media_list.sort(key=get_year_for_sort)
    else:
        all_media_list.sort(key=lambda m: m.title.lower())
    
    all_tags = Tag.query.order_by(Tag.name).all()

    return render_template('index.html', 
                           all_media=all_media_list, 
                           all_tags=all_tags,
                           current_sort=sort_by, 
                           current_filter=filter_type,
                           current_tag=tag_filter)

@main.route('/media/<int:media_id>')
def media_page(media_id):
    media_item = Media.query.get_or_404(media_id)
    return render_template('media_page.html', media=media_item, get_rating_class=get_rating_class)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def save_file(file_storage):
    from flask import current_app
    filename = secure_filename(file_storage.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file_storage.save(file_path)
    return filename

@main.route('/edit_media/<int:media_id>', methods=['GET', 'POST'])
@login_required
def edit_media(media_id):
    media = Media.query.get_or_404(media_id)
    form = MediaForm(obj=media)
    all_tags = Tag.query.order_by(Tag.name).all()
    media_tag_ids = [tag.id for tag in media.tags]

    if form.validate_on_submit():
        media.media_type = form.media_type.data
        media.title = form.title.data
        media.creator = form.creator.data
        media.years = form.years.data
        media.official_rating = form.official_rating.data

        if form.poster_img.data:
            media.poster_img = save_file(form.poster_img.data)
        if form.banner_img.data:
            media.banner_img = save_file(form.banner_img.data)

        delete_stmt = media_tags.delete().where(media_tags.c.media_id == media.id)
        db.session.execute(delete_stmt)

        selected_tag_ids = request.form.getlist('tags', type=int)
        for tag_id in selected_tag_ids:
            insert_stmt = media_tags.insert().values(media_id=media.id, tag_id=tag_id)
            db.session.execute(insert_stmt)

        if media.media_type == 'tv_show':
            for track in media.tracks: db.session.delete(track)
        elif media.media_type == 'album':
            for season in media.seasons: db.session.delete(season)
        
        db.session.commit()
        
        if media.media_type == 'tv_show':
            Season.query.filter_by(media_id=media.id).delete()
            for s_key, s_val in request.form.items():
                if s_key.startswith('season_number_'):
                    s_idx = s_key.split('_')[-1]
                    
                    # --- NEW: Get season-specific data from form ---
                    season_rating_str = request.form.get(f'season_rating_{s_idx}', '')
                    season_rating = float(season_rating_str) if season_rating_str else None
                    season_year = request.form.get(f'season_year_{s_idx}', '')

                    new_season = Season(
                        season_number=int(s_val), 
                        rating=season_rating, 
                        year=season_year,
                        media_id=media.id
                    )
                    db.session.add(new_season)
                    db.session.flush()

                    for e_key, e_val in request.form.items():
                        if e_key.startswith(f'ep_number_{s_idx}_'):
                            e_idx = e_key.split('_')[-1]
                            ep_title = request.form.get(f'ep_title_{s_idx}_{e_idx}', '')
                            ep_rating_str = request.form.get(f'ep_rating_{s_idx}_{e_idx}', '')
                            ep_rating = float(ep_rating_str) if ep_rating_str else None
                            new_ep = Episode(episode_number=int(e_val), title=ep_title, rating=ep_rating, season_id=new_season.id)
                            db.session.add(new_ep)
        
        elif media.media_type == 'album':
            Track.query.filter_by(media_id=media.id).delete()
            for t_key, t_val in request.form.items():
                if t_key.startswith('track_number_'):
                    t_idx = t_key.split('_')[-1]
                    track_title = request.form.get(f'track_title_{t_idx}', '')
                    track_rating_str = request.form.get(f'track_rating_{t_idx}', '')
                    track_rating = float(track_rating_str) if track_rating_str else None
                    new_track = Track(track_number=int(t_val), title=track_title, rating=track_rating, media_id=media.id)
                    db.session.add(new_track)

        db.session.commit()
        flash('Media updated!', 'success')
        return redirect(url_for('main.media_page', media_id=media.id))
        
    return render_template('edit_media.html', 
                           form=form, 
                           media=media, 
                           all_tags=all_tags,
                           media_tag_ids=media_tag_ids)

@main.route('/add_media', methods=['GET', 'POST'])
@login_required
def add_media():
    form = MediaForm()
    if form.validate_on_submit():
        new_media = Media(
            media_type=form.media_type.data,
            title=form.title.data,
            creator=form.creator.data,
            years=form.years.data,
            official_rating=form.official_rating.data
        )
        if form.poster_img.data:
            new_media.poster_img = save_file(form.poster_img.data)
        if form.banner_img.data:
            new_media.banner_img = save_file(form.banner_img.data)
        
        db.session.add(new_media)
        db.session.commit()
        flash('New media created. You can now add episodes/tracks and tags.', 'success')
        return redirect(url_for('main.edit_media', media_id=new_media.id))
    
    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template('edit_media.html', form=form, media=None, all_tags=all_tags, media_tag_ids=[])

@main.route('/delete_media/<int:media_id>', methods=['POST'])
@login_required
def delete_media(media_id):
    media_to_delete = Media.query.get_or_404(media_id)
    
    delete_stmt = media_tags.delete().where(media_tags.c.media_id == media_id)
    db.session.execute(delete_stmt)
    
    db.session.delete(media_to_delete)
    db.session.commit()
    flash('Media has been deleted.', 'success')
    return redirect(url_for('main.index'))
