from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, UserPostForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from werkzeug.urls import url_parse
from datetime import datetime

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = UserPostForm()
    if form.validate_on_submit():
        new_post = Post(body=form.body.data, author=current_user)
        db.session.add(new_post)
        db.session.commit()
        flash('Your post has been published.')
        return redirect(url_for('index'))

    page_number = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page_number,
        app.config['POSTS_PER_PAGE'],
        False
    )
    post_items = posts.items
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None

    return render_template(
        'index.html',
        title='Home',
        posts=post_items,
        next_url=next_url,
        prev_url=prev_url,
        form=form
    )

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Congratulations! You have now registered')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data

        user = User.query.filter_by(username=username).first()
        print('user is', user)
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=remember_me)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            return redirect(url_for('index'))
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    avatar_size = 128
    random_avatar = 'https://source.unsplash.com/random/{}x{}'.format(avatar_size, avatar_size)
    return render_template('about.html', title='About Us', avatar=random_avatar);


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page_number = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page_number, app.config['POSTS_PER_PAGE'], False
    )
    post_items = posts.items
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template(
        'user.html', user=user, posts=post_items, next_url=next_url, prev_url=prev_url,
    )

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    current_username = current_user.username
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} can not be found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You can not follow yourself!')
        return redirect(url_for('index'))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} can not be found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You can not unfollow yourself!')
        return redirect(url_for('index'))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are no longer following {}'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/explore')
def explore():
    page_number = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page_number, app.config['POSTS_PER_PAGE'], False
    )
    post_items = posts.items
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template(
        'index.html',
        title='Explore',
        posts=post_items,
        next_url=next_url,
        prev_url=prev_url
    );

