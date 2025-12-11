from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db, cache
from models import Club, Post, RSVP, ClubFollower, PostLike
from datetime import datetime, timezone

student = Blueprint('student', __name__)

# --- Helper Functions ---

def check_student_role():
    # Allow Student, Club, and Admin roles to view the student pages
    if current_user.role not in ['student', 'club', 'admin']:
        flash('Access denied.', 'danger')
        return False
    return True

def make_cache_key(*args, **kwargs):
    path = request.path
    uid = current_user.id if current_user.is_authenticated else 'guest'
    return f"{path}_{uid}"

# --- Dashboard & Feeds ---
# blueprints/student.py

@student.route('/dashboard')
@login_required
def dashboard():
    if not check_student_role():
        return redirect(url_for('index'))
    
    # Start the query
    query = Post.query.join(Club).filter(Club.verified == True)
    
    # --- NEW: SEARCH LOGIC ---
    search_query = request.args.get('q')
    if search_query:
        query = query.filter(
            (Post.event_title.ilike(f'%{search_query}%')) | 
            (Post.caption.ilike(f'%{search_query}%')) |
            (Club.name.ilike(f'%{search_query}%'))
        )
    # -------------------------

    # Execute query with sort
    posts = query.order_by(Post.created_at.desc()).all()
    
    # Metadata
    user_rsvps = {rsvp.post_id for rsvp in current_user.rsvps}
    followed_club_ids = {follow.club_id for follow in current_user.followed_clubs}
    user_likes = {like.post_id for like in PostLike.query.filter_by(user_id=current_user.id).all()}
    
    return render_template('student/dashboard.html', 
                         events=posts, 
                         user_rsvps=user_rsvps,
                         followed_club_ids=followed_club_ids,
                         user_likes=user_likes,
                         feed_type='global',
                         search_query=search_query) # Pass query back to template

@student.route('/following')
@login_required
def following_feed():
    """Subscribed Feed: Shows Posts ONLY from clubs the user follows."""
    if not check_student_role():
        return redirect(url_for('index'))

    # 1. Get IDs of clubs the user follows
    followed_club_ids = [f.club_id for f in current_user.followed_clubs]

    # 2. Query posts from those clubs only
    posts = Post.query.filter(
        Post.club_id.in_(followed_club_ids)
    ).order_by(Post.created_at.desc()).all()

    user_rsvps = {rsvp.post_id for rsvp in current_user.rsvps}
    user_likes = {like.post_id for like in PostLike.query.filter_by(user_id=current_user.id).all()}
    
    return render_template('student/dashboard.html', 
                         events=posts, 
                         user_rsvps=user_rsvps,
                         followed_club_ids=set(followed_club_ids),
                         user_likes=user_likes,
                         feed_type='following')

@student.route('/my-rsvps')
@login_required
def my_rsvps():
    """My Schedule: Shows only 'Event' type posts the user has RSVP'd to."""
    if not check_student_role():
        return redirect(url_for('index'))
    
    # Query RSVPs -> Join Post -> Filter by User
    rsvp_posts = Post.query.join(RSVP).filter(
        RSVP.user_id == current_user.id
    ).order_by(Post.event_date).all()
    
    return render_template('student/my_rsvps.html', events=rsvp_posts)

# --- NEW: API Route for Calendar (FIXES YOUR ISSUE) ---
@student.route('/api/my-rsvps')
@login_required
def get_rsvp_events_json():
    """API endpoint for FullCalendar"""
    # Get user's RSVPs
    rsvp_posts = Post.query.join(RSVP).filter(
        RSVP.user_id == current_user.id
    ).all()
    
    events_data = []
    for post in rsvp_posts:
        # Only add to calendar if it's an event with a valid date
        if post.is_event and post.event_date:
            events_data.append({
                'title': post.event_title,
                'start': post.event_date.isoformat(), # Formats date for JS
                'url': url_for('student.event_detail', post_id=post.id),
                'color': '#0d6efd' # Bootstrap Primary Blue
            })
            
    return jsonify(events_data)

# --- Interactions ---

@student.route('/event/<int:post_id>')
@login_required
def event_detail(post_id):
    if not check_student_role():
        return redirect(url_for('index'))
    
    post = Post.query.get_or_404(post_id)
    
    has_rsvp = RSVP.query.filter_by(user_id=current_user.id, post_id=post_id).first() is not None
    is_following = ClubFollower.query.filter_by(user_id=current_user.id, club_id=post.club_id).first() is not None
    rsvp_count = RSVP.query.filter_by(post_id=post_id).count()
    
    return render_template('student/event_detail.html', 
                         event=post, 
                         has_rsvp=has_rsvp,
                         is_following=is_following,
                         rsvp_count=rsvp_count)

@student.route('/rsvp/<int:post_id>', methods=['POST'])
@login_required
def toggle_rsvp(post_id):
    if not check_student_role():
        return redirect(url_for('index'))

    post = Post.query.get_or_404(post_id)
    
    if not post.is_event:
        flash('This post is not an event.', 'warning')
        return redirect(request.referrer)

    existing_rsvp = RSVP.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_rsvp:
        db.session.delete(existing_rsvp)
        flash('RSVP removed', 'info')
    else:
        rsvp = RSVP(user_id=current_user.id, post_id=post_id)
        db.session.add(rsvp)
        flash('RSVP confirmed!', 'success')
    
    db.session.commit()
    return redirect(request.referrer or url_for('student.dashboard'))

@student.route('/follow/<int:club_id>', methods=['POST'])
@login_required
def toggle_follow(club_id):
    if not check_student_role():
        return redirect(url_for('index'))

    club = Club.query.get_or_404(club_id)
    existing_follow = ClubFollower.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    
    if existing_follow:
        db.session.delete(existing_follow)
        flash(f'Unfollowed {club.name}', 'info')
    else:
        follow = ClubFollower(user_id=current_user.id, club_id=club_id)
        db.session.add(follow)
        flash(f'Now following {club.name}!', 'success')
    
    db.session.commit()
    return redirect(request.referrer or url_for('student.dashboard'))

# --- NEW: Like Feature API ---
@student.route('/like/<int:post_id>', methods=['POST'])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    like = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    
    liked = False
    if like:
        db.session.delete(like)
        liked = False
    else:
        new_like = PostLike(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        liked = True
        
    db.session.commit()
    
    return jsonify({
        'likes_count': len(post.likes),
        'liked': liked
    })

# --- Club Pages ---

@student.route('/clubs')
@login_required
def browse_clubs():
    all_clubs = Club.query.all()
    return render_template('student/browse_clubs.html', clubs=all_clubs)

@student.route('/club/<string:club_name_slug>')
@login_required
def club_detail(club_name_slug):
    if not check_student_role():
        return redirect(url_for('index'))
    
    club_name = club_name_slug.replace('_', ' ')
    club = Club.query.filter_by(name=club_name).first_or_404()
    
    is_following = ClubFollower.query.filter_by(user_id=current_user.id, club_id=club.id).first() is not None
    
    upcoming_events = Post.query.filter(
        Post.club_id == club.id,
        Post.is_event == True,
        Post.event_date >= datetime.now(timezone.utc)
    ).order_by(Post.event_date).all()
    
    follower_count = ClubFollower.query.filter_by(club_id=club.id).count()
    
    return render_template('student/club_detail.html',
                           club=club,
                           is_following=is_following,
                           upcoming_events=upcoming_events,
                           follower_count=follower_count)

@student.route('/my-clubs')
@login_required
def my_clubs():
    followed_clubs = Club.query.join(ClubFollower).filter(
        ClubFollower.user_id == current_user.id,
        Club.verified == True
    ).all()
    
    return render_template('student/my_clubs.html', clubs=followed_clubs)