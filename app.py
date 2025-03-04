import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from config import Config
from models import db, User, Post, Like, Comment

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Configure Cloudinary
cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET']
)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

from flask import send_from_directory

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Basic validation
        if not username or not email or not password:
            flash('All fields are required.')
            return redirect(url_for('register'))
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now registered!')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('feed')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/feed')
@login_required
def feed():
    # Get posts from users that the current user follows
    followed_users = [user.id for user in current_user.followed.all()]
    followed_users.append(current_user.id)  # Include current user's posts
    
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter(Post.user_id.in_(followed_users)).order_by(
        Post.timestamp.desc()).paginate(page=page, per_page=10)
    
    return render_template('feed.html', posts=posts)

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template('feed.html', posts=posts, title="Explore")

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['photo']
        caption = request.form.get('caption', '')
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        # Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(file)
            image_url = upload_result.get('secure_url')
            
            # Create new post
            post = Post(image_url=image_url, caption=caption, author=current_user)
            db.session.add(post)
            db.session.commit()
            
            flash('Your photo has been uploaded!')
            return redirect(url_for('profile', username=current_user.username))
        except Exception as e:
            flash(f'Error uploading image: {str(e)}')
            return redirect(request.url)
    
    return render_template('post.html')

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id=user.id).order_by(
        Post.timestamp.desc()).paginate(page=page, per_page=9)
    
    return render_template('profile.html', user=user, posts=posts)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('profile', username=username))
    
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {username}!')
    return redirect(url_for('profile', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('profile', username=username))
    
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You have unfollowed {username}.')
    return redirect(url_for('profile', username=username))

@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if like:
        # Unlike the post
        db.session.delete(like)
        db.session.commit()
        return jsonify({'success': True, 'action': 'unliked', 'likes': post.likes.count()})
    else:
        # Like the post
        like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'success': True, 'action': 'liked', 'likes': post.likes.count()})

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)
    comment_text = request.form.get('comment')
    
    if not comment_text:
        return jsonify({'success': False, 'error': 'Comment cannot be empty'})
    
    comment = Comment(body=comment_text, user_id=current_user.id, post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'body': comment.body,
            'username': current_user.username,
            'timestamp': comment.timestamp.strftime('%Y-%m-%d %H:%M')
        }
    })

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if the current user is the author of the post
    if post.user_id != current_user.id:
        abort(403)
    
    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted.')
    return redirect(url_for('profile', username=current_user.username))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio', '')
        
        if 'profile_pic' in request.files and request.files['profile_pic'].filename:
            try:
                upload_result = cloudinary.uploader.upload(request.files['profile_pic'])
                current_user.profile_pic = upload_result.get('secure_url')
            except Exception as e:
                flash(f'Error uploading profile picture: {str(e)}')
        
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('profile', username=current_user.username))
    
    return render_template('edit_profile.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error_code=500, message="Internal server error"), 500

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Create a demo user if no users exist
    if User.query.count() == 0:
        demo_user = User(
            username='demo',
            email='demo@example.com',
            bio='This is a demo account for the Instagram clone app.'
        )
        demo_user.set_password('password')
        db.session.add(demo_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
