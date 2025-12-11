from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Club, User, Post  # Added Post
from extensions import db

admin_bp = Blueprint('admin', __name__)

def check_admin_role():
    if current_user.role != 'admin':
        flash('Access denied. Admin account required.', 'danger')
        return False
    return True

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_admin_role():
        return redirect(url_for('index'))
    
    total_users = User.query.count()
    total_clubs = Club.query.count()
    
    # Pending approvals logic
    pending_clubs = Club.query.filter(
        (Club.verified == False) | 
        ((Club.officer_verified == False) & (Club.owner_id != None))
    ).all()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_clubs=total_clubs,
                         pending_clubs=pending_clubs)

@admin_bp.route('/verify_club/<int:club_id>')
@login_required
def verify_club(club_id):
    if not check_admin_role():
        return redirect(url_for('index'))
        
    club = Club.query.get_or_404(club_id)
    club.verified = True
    club.officer_verified = True
    db.session.commit()
    flash(f'{club.name} and its officer have been verified!', 'success')
    return redirect(url_for('admin.dashboard'))

# --- NEW: User Management Routes ---

@admin_bp.route('/users')
@login_required
def manage_users():
    """List all users for management"""
    if not check_admin_role(): return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:user_id>/edit_role', methods=['POST'])
@login_required
def edit_user_role(user_id):
    """Change a user's role"""
    if not check_admin_role(): return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in ['student', 'club', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'Role for {user.email} updated to {new_role}.', 'success')
    else:
        flash('Invalid role selected.', 'danger')
        
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user account"""
    if not check_admin_role(): return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent Admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account while logged in.', 'danger')
        return redirect(url_for('admin.manage_users'))
        
    db.session.delete(user)
    db.session.commit()
    flash('User account deleted.', 'success')
    return redirect(url_for('admin.manage_users'))

# --- NEW: Feed Management Route ---

@admin_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Admin force delete a post"""
    if not check_admin_role(): return redirect(url_for('index'))
    
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post removed successfully.', 'info')
    
    # Redirect back to where they came from (likely the feed)
    return redirect(request.referrer or url_for('student.dashboard'))