import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Club, Post, ClubFollower
from extensions import db
from datetime import datetime

club_bp = Blueprint('club', __name__)

def check_club_role():
    if current_user.role != 'club' and current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return False
    return True

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/posts', picture_fn)
    form_picture.save(picture_path)
    return picture_fn

@club_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_club_role(): return redirect(url_for('index'))
    if not current_user.club: return redirect(url_for('club.onboarding'))
    
    my_club = current_user.club
    real_follower_count = ClubFollower.query.filter_by(club_id=my_club.id).count()
    return render_template('club/dashboard.html', club=my_club, real_follower_count=real_follower_count)

@club_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not check_club_role() or not current_user.club: return redirect(url_for('club.dashboard'))
    club = current_user.club
    
    if request.method == 'POST':
        club.description = request.form.get('description')
        club.meeting_time = request.form.get('meeting_time')
        club.location = request.form.get('location')
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                club.image_file = save_picture(file)
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('club.dashboard'))
    return render_template('club/settings.html', club=club)

@club_bp.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    if not check_club_role(): return redirect(url_for('index'))
    if current_user.club: return redirect(url_for('club.dashboard'))

    if request.method == 'POST':
        club_name = request.form.get('name')
        category = request.form.get('category')
        desc = request.form.get('description')
        existing = Club.query.filter_by(name=club_name).first()

        if existing:
            if existing.owner_id:
                flash('Club already claimed.', 'danger')
            else:
                existing.owner_id = current_user.id
                existing.verified = True
                existing.officer_verified = False
                existing.description = desc
                db.session.commit()
                flash(f'Claimed {club_name}. Wait for verification.', 'warning')
                return redirect(url_for('club.dashboard'))
        else:
            new_club = Club(name=club_name, category=category, description=desc, owner_id=current_user.id, verified=False, officer_verified=False, member_count=1)
            db.session.add(new_club)
            db.session.commit()
            flash('Club created. Wait for verification.', 'success')
            return redirect(url_for('club.dashboard'))
    return render_template('club/onboarding.html')

@club_bp.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if not check_club_role() or not current_user.club: return redirect(url_for('club.dashboard'))
    if not current_user.club.officer_verified:
        flash('Officer status pending.', 'danger')
        return redirect(url_for('club.dashboard'))
    
    if request.method == 'POST':
        caption = request.form.get('caption')
        is_event = 'is_event' in request.form
        image_file = 'default.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '': image_file = save_picture(file)

        new_post = Post(club_id=current_user.club.id, caption=caption, image_file=image_file, is_event=is_event)
        
        if is_event:
            new_post.event_title = request.form.get('event_title')
            new_post.event_location = request.form.get('location')
            date_str = request.form.get('date')
            if date_str:
                try: new_post.event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
                except: new_post.event_date = datetime.now()

        db.session.add(new_post)
        db.session.commit()
        flash('Posted!', 'success')
        return redirect(url_for('club.dashboard'))
    return render_template('club/create_event.html')

@club_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    if not check_club_role() or not current_user.club: return redirect(url_for('index'))
    post = Post.query.get_or_404(post_id)
    if post.club_id != current_user.club.id: return redirect(url_for('club.dashboard'))
        
    if request.method == 'POST':
        post.caption = request.form.get('caption')
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '': post.image_file = save_picture(file)
        post.is_event = 'is_event' in request.form
        if post.is_event:
            post.event_title = request.form.get('event_title')
            post.event_location = request.form.get('location')
            date_str = request.form.get('date')
            if date_str:
                try: post.event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
                except: pass 
        db.session.commit()
        flash('Updated!', 'success')
        return redirect(url_for('club.dashboard'))
    return render_template('club/edit_post.html', post=post)

@club_bp.route('/followers')
@login_required
def manage_followers():
    if not check_club_role() or not current_user.club: return redirect(url_for('club.dashboard'))
    followers = ClubFollower.query.filter_by(club_id=current_user.club.id).all()
    return render_template('club/followers.html', followers=followers)

@club_bp.route('/remove_follower/<int:user_id>', methods=['POST'])
@login_required
def remove_follower(user_id):
    if not check_club_role() or not current_user.club: return redirect(url_for('index'))
    follow = ClubFollower.query.filter_by(club_id=current_user.club.id, user_id=user_id).first_or_404()
    db.session.delete(follow)
    db.session.commit()
    flash('Removed follower.', 'info')
    return redirect(url_for('club.manage_followers'))

@club_bp.route('/post/<int:post_id>/rsvps')
@login_required
def post_rsvps(post_id):
    if not check_club_role() or not current_user.club: return redirect(url_for('index'))
    post = Post.query.get_or_404(post_id)
    if post.club_id != current_user.club.id: return redirect(url_for('club.dashboard'))
    return render_template('club/post_rsvps.html', post=post)