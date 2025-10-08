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
    tag_filter = request.args.get('tag', 'all') # NEW tag filter

    query = Media.query

    if filter_type != 'all':
        query = query.filter(Media.media_type == filter_type)

    # --- NEW: Filter by tag ---
    if tag_filter != 'all':
        try:
            tag_id = int(tag_filter)
            # Find all media_ids from the association table that have this tag_id
            media_ids_with_tag = db.session.query(media_tags.c.media_id).filter_by(tag_id=tag_id)
            # Filter the main query to only include those media items
            query = query.filter(Media.id.in_([item[0] for item in media_ids_with_tag]))
        except (ValueError, TypeError):
            pass # Ignore if tag is not a valid number
    
    all_media_list = query.all()

    if sort_by == 'score_desc':
        all_media_list.sort(key=lambda m: m.overall_score, reverse=True)
    elif sort_by == 'score_asc':
        all_media_list.sort(key=lambda m: m.overall_score)
    else:
        all_media_list.sort(key=lambda m: m.title.lower())
    
    all_tags = Tag.query.order_by(Tag.name).all() # Get all tags for the dropdown

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

        # --- NEW: Process tag data ---
        # 1. Clear existing tag associations for this media item
        delete_stmt = media_tags.delete().where(media_tags.c.media_id == media.id)
        db.session.execute(delete_stmt)

        # 2. Get selected tags from the form and create new associations
        selected_tag_ids = request.form.getlist('tags', type=int)
        for tag_id in selected_tag_ids:
            insert_stmt = media_tags.insert().values(media_id=media.id, tag_id=tag_id)
            db.session.execute(insert_stmt)

        if media.media_type == 'tv_show':
            for track in media.tracks: db.session.delete(track)
        elif media.media_type == 'album':
            for season in media.seasons: db.session.delete(season)
        
        db.session.commit()
        
        # ... (rest of the route for seasons/tracks remains the same) ...
        
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
    
    # Also pass tags to the add_media page
    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template('edit_media.html', form=form, media=None, all_tags=all_tags, media_tag_ids=[])

@main.route('/delete_media/<int:media_id>', methods=['POST'])
@login_required
def delete_media(media_id):
    media_to_delete = Media.query.get_or_404(media_id)
    
    # Manually delete tag associations from the 'tags' database
    delete_stmt = media_tags.delete().where(media_tags.c.media_id == media_id)
    db.session.execute(delete_stmt)
    
    db.session.delete(media_to_delete)
    db.session.commit()
    flash('Media has been deleted.', 'success')
    return redirect(url_for('main.index'))
