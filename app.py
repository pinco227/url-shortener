import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from models import User
from utils import generate_short_url
from forms import (LoginForm, RegisterForm, ProfileForm, CreateURLForm, SearchForm)

# For Development environment, env.py must be set, for Production, environmental variables must be set by system
if os.path.exists('env.py'):
  import env

# Database connection details
db_file = os.environ.get('DATABASE_URL')

# App Configuration
app = Flask(__name__)

# Config app
config = {
  'SECRET_KEY': os.environ.get('SECRET_KEY'),
  'RECAPTCHA_PUBLIC_KEY': os.environ.get('RC_SITE_KEY'),
  'RECAPTCHA_PRIVATE_KEY': os.environ.get('RC_SECRET_KEY'),
}
app.config.update(config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# Connect to the database
def connect_db():
  conn = sqlite3.connect(db_file)
  conn.row_factory = sqlite3.Row
  return conn

# Create DB method - Created DB and Table if not exists
def create_db():
  # Establish DB connection
  conn = connect_db()
  cursor = conn.cursor()

  # Create users table
  cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    fname TEXT NOT NULL,
                    lname TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NULL,
                    website TEXT,
                    last_login DATETIME DEFAULT NULL,
                    last_failed_login DATETIME DEFAULT NULL,
                    failed_login_attempts INTEGER DEFAULT 0
                  )""")

  # Create urls table
  cursor.execute("""CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_url TEXT NOT NULL,
                    shortened_url TEXT UNIQUE NOT NULL,
                    user_id INTEGER REFERENCES users(id),
                    clicks INTEGER DEFAULT 0
                  )""")

  conn.commit()
  # Close DB connection
  conn.close()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
  try:
    # Establish DB connection
    conn = connect_db()
    cursor = conn.cursor()
    # Get user data fron DB, using user_id method parameter
    query = "SELECT * FROM users WHERE id = ? LIMIT 1"
    cursor.execute(query, (user_id,))
    user_row = cursor.fetchone()
  except sqlite3.Error as e:
    print(e) # Log error to server only
  finally:
    if conn:
      # Close DB connection
      conn.close()
    if user_row:
      # Create and return User object if user exists
      return User(user_row['id'], user_row['username'], user_row['password'], user_row['fname'], user_row['lname'], user_row['email'], user_row['phone'], user_row['website'])
  # If DB failed or User not found, return None
  return None

# Homepage Route - Welcome message for new users, Dashboard for logged users
@app.route('/')
def index():
  # Check if user is logged in
  if current_user.is_authenticated and current_user.get_id():
    # initialize statistics variable
    stats = {'urls': 0, 'clicks': 0}
    try:
      # establish db connection
      conn = connect_db()
      cursor = conn.cursor()
      # count user's URLs
      query = "SELECT Count() FROM urls WHERE user_id = ?"
      cursor.execute(query, (current_user.get_id(),))
      urls = cursor.fetchone()[0]
      stats['urls'] = urls
      # count user's total Clicks
      query_clicks = "SELECT SUM(clicks) AS total_clicks FROM urls WHERE user_id = ?"
      cursor.execute(query_clicks, (current_user.get_id(),))
      clicks = cursor.fetchone()[0]
      stats['clicks'] = clicks
    except sqlite3.Error as e:
      print(e) # Log error to server only
      flash("Database error!", "error")
    finally:
      if conn:
        # Close DB connection
        conn.close()
    # send stats variable to index page
    return render_template('index.html', stats=stats)
  else:
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
  # If user already logged in, redirect to home
  if current_user.is_authenticated:
    flash("You are already logged in.", "info")
    return redirect(url_for('index'))

  # Initialize form
  form = LoginForm()
  # Process POST data
  if request.method == 'POST':
    # Validate form data
    if form.validate_on_submit():
      loggedin = False
      current_time = datetime.utcnow()
      username = form.username.data
      password = form.password.data
      try:
        # Establish DB connection
        conn = connect_db()
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE username = ? LIMIT 1"
        cursor.execute(query, (username,))
        user_row = cursor.fetchone()
        # Check if user exists and password hash matches
        if user_row and bcrypt.check_password_hash(user_row['password'], password):
          thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
          last_failed_login = datetime.strptime(user_row['last_failed_login'], '%Y-%m-%d %H:%M:%S.%f')
          if user_row['failed_login_attempts'] > 4 and last_failed_login >= thirty_minutes_ago:
            time_elapsed = current_time - last_failed_login
            remaining_minutes = (timedelta(minutes=30) - time_elapsed).total_seconds() / 60
            flash(f"Too many failed attempts. Account locked for {int(remaining_minutes)} minutes.", "error")
          else:
            # Create User object
            user = User(user_row['id'], user_row['username'], user_row['password'], user_row['fname'], user_row['lname'], user_row['email'], user_row['phone'], user_row['website'])
            # Login user using Flask Login
            login_user(user)
            loggedin = True
            flash("Successfully logged in!", "success")
            query_log = "UPDATE users SET last_login = ?, failed_login_attempts = 0 WHERE id = ?"
            cursor.execute(query_log, (current_time, user_row['id']))
            conn.commit()
        elif not user_row:
          flash("User not found. Please register!", "error")
        else:
          flash("Invalid credentials. Try again!", "error")
          flash("Account will be locked for 30 minutes after 5 failed attempts!", "info")
          query_log = "UPDATE users SET failed_login_attempts = failed_login_attempts + 1, last_failed_login = ? WHERE id = ?"
          cursor.execute(query_log, (current_time, user_row['id']))
          conn.commit()
      except sqlite3.Error as e:
        print(e) # Log error to server only
        flash("Database error!", "error")
      finally:
        if conn:
          # Close DB connection
          conn.close()
        if loggedin:
          # If logged in successfully, redirect to index
          return redirect(url_for('index'))
    else:
      flash("Invalid data! Check fields and try again.", "error")
  # If method is not POST, or submitted data is not correct, render login page
  return render_template('login.html', form=form)

# Logout route
@app.route('/logout')
def logout():
  logout_user()
  flash("Successfully logged out!", "info")
  return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
  # If user already logged in, redirect to home
  if current_user.is_authenticated:
    flash("You are already logged in.", "info")
    return redirect(url_for('index'))

  # Initialize form
  form = RegisterForm()
  # Process POST data
  if request.method == 'POST':
    # Validate form data
    if form.validate_on_submit():
      signedup = False
      try:
        username = form.username.data
        # Generate password hash
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        fname = form.fname.data
        lname = form.lname.data
        email = form.email.data
        phone = form.phone.data
        website = form.website.data
        # Establish DB connection
        conn = connect_db()
        cursor = conn.cursor()
        # Insert new user into DB
        query = "INSERT INTO users (username, password, fname, lname, email, phone, website) VALUES (?, ?, ?, ?, ?, ?, ?)"
        cursor.execute(query, (username, password, fname, lname, email, phone, website))
        conn.commit()
        signedup = True
      except sqlite3.Error as e:
        print(e) # Log error to server only
        flash("Database error!", "error")
        signedup = False
      finally:
        if conn:
          # Close DB connection
          conn.close()
        if signedup:
          flash("Successfully registered! Please Log in!", "success")
          # If registered successfully, redirect to login
          return redirect(url_for('login'))
        else:
          flash("Failed to register. Try again!", "error")
    else:
      flash("Invalid data! Check fields and try again.", "error")
  # If method is not POST, or submitted data is not correct, render register page
  return render_template('register.html', form=form)

# Profile route
@app.route('/profile')
@app.route('/profile/<user_id>')
def profile(user_id = None):
  # If no user_id provided and user is logged in, show self profile
  if user_id is None and current_user.is_authenticated and current_user.get_id():
    user=current_user
    return render_template('profile.html', user=current_user)
  # if user_id is provided, load user and show profile
  elif user_id is not None:
    user = load_user(user_id)
    urls = None
    if not user:
      flash("User not found!", "error")
    else:
      try:
        # Establish DB connection
        conn = connect_db()
        cursor = conn.cursor()
        # Get URLs of user
        query = "SELECT * FROM urls WHERE user_id = ?"
        cursor.execute(query, (user_id,))
        urls = cursor.fetchall()
      except sqlite3.Error as e:
        print(e) # Log error to server only
        flash("Database error!", "error")
      finally:
        if conn:
          # Close DB connection
          conn.close()
    return render_template('profile.html', user=user, urls=urls)
  # If user is not logged in and no user_id is provided, redirect home with message
  else:
    flash("Authentication needed. Please login or register!", "error")
    return redirect(url_for('index'))

# Edit profile route
@app.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
  # Check if user is logged in
  if current_user.is_authenticated and current_user.get_id():
    # Initialize form
    form = ProfileForm()
    # Process form data
    if request.method == 'POST':
      # Validate form data
      if form.validate_on_submit():
        updated = False
        try:
          fname = form.fname.data
          lname = form.lname.data
          email = form.email.data
          phone = form.phone.data
          website = form.website.data
          # Establish DB connection
          conn = connect_db()
          cursor = conn.cursor()
          # Update user in database with submitted data
          query = "UPDATE users SET fname=?, lname=?, email=?, phone=?, website=? WHERE username=?"
          cursor.execute(query, (fname, lname, email, phone, website, current_user.username))
          conn.commit()
          updated = True
        except sqlite3.Error as e:
          print(e) # Log error to server only
          flash("Database error!", "error")
          updated = False
        finally:
          if conn:
            # Close DB connection
            conn.close()
          if updated:
            current_user.fname = fname
            current_user.lname = lname
            current_user.email = email
            current_user.phone = phone
            current_user.website = website
            flash("Profile successfully updated!", "success")
            # If database updated successfully, redirect to profile with message
            return redirect(url_for('profile'))
          else:
            flash("Failed to update. Try again!", "error")
      else:
        flash("Invalid data! Check fields and try again.", "error")
    # If method is not POST or submitted data is incorrect, render profile edit page
    return render_template('profile_edit.html', form=form)
  # If user is not logged in, redirect to index with error message
  flash("Authentication needed. Please login or register!", "error")
  return redirect(url_for('index'))

# My URLs route
@app.route('/my-urls')
def my_urls():
  # Check if user is logged in
  if current_user.is_authenticated and current_user.get_id():
    try:
      # Establish DB connection
      conn = connect_db()
      cursor = conn.cursor()
      # Get URLs of user
      query = "SELECT * FROM urls WHERE user_id = ?"
      cursor.execute(query, (current_user.get_id(),))
      urls = cursor.fetchall()
    except sqlite3.Error as e:
      print(e) # Log error to server only
      flash("Database error!", "error")
    finally:
      if conn:
        # Close DB connection
        conn.close()
      if urls:
        return render_template('my_urls.html', urls=urls)
      return render_template('my_urls.html')
  redirect(url_for('index'))

# Create Short URL route
@app.route('/shorten', methods=['GET','POST'])
def shorten():
  # Check if user is logged in
  if current_user.is_authenticated and current_user.get_id():
    # Initialize form
    form = CreateURLForm()
    # Process form data
    if request.method == 'POST':
      # Validate form data
      if form.validate_on_submit():
        created = False
        try:
          original_url = form.original_url.data
          # Generate short URL
          shortened_url = generate_short_url()
          # Establish DB connection
          conn = connect_db()
          cursor = conn.cursor()
          # Add url to db linking original_url with generated short URL
          query = "INSERT INTO urls (original_url, shortened_url, user_id) VALUES (?, ?, ?)"
          cursor.execute(query, (original_url, shortened_url, current_user.id))
          conn.commit()
          created = True
        except sqlite3.Error as e:
          print(e) # Log error to server only
          flash("Database error!", "error")
          created = False
        finally:
          if conn:
            # Close DB connection
            conn.close()
          if created:
            flash("URL " + shortened_url + " created successfully", "success")
            # If URL successfully generated and added to DB, redirect to user's URLs with message
            return redirect(url_for('my_urls'))
          else:
            flash("Failed to create short URL!", "error")
      else:
        flash("Invalid data! Check fields and try again.", "error")
    # If Method is not POST or submitted data is not valid, render Create URL form
    return render_template('create_url.html', form=form)
  # If user is not logged in, redirect to home page with error message
  flash("Authentication needed. Please login or register!", "error")
  return redirect(url_for('index'))

# Search URLs route
@app.route('/search')
def search():
  search_query = None
  form = SearchForm(request.args)
  if 'q' in request.args and form.validate():
    search_query = form.q.data
    try:
      # Establish DB connection
      conn = connect_db()
      cursor = conn.cursor()
      # Get URLs of query
      db_query = """SELECT urls.shortened_url, urls.original_url, urls.clicks, urls.user_id, users.username
                    FROM urls
                    JOIN users ON urls.user_id = users.id
                    WHERE urls.original_url LIKE ? OR users.username LIKE ?;"""
      cursor.execute(db_query, (f'%{search_query}%', f'%{search_query}%'))
      urls = cursor.fetchall()
    except sqlite3.Error as e:
      print(e) # Log error to server only
      flash("Database error!", "error")
    finally:
      if conn:
        # Close DB connection
        conn.close()
      if urls:
        return render_template('search.html', form=form, urls=urls, query=search_query)
      return render_template('search.html', form=form, query=search_query)
  return render_template('search.html', form=form)

# Route to redirect and track clicks
@app.route('/<shortened_url>')
def redirect_url(shortened_url):
  try:
    # Establish DB connection
    conn = connect_db()
    cursor = conn.cursor()
    # Get DB entry of the short URL in route
    query = "SELECT * FROM urls WHERE shortened_url = ? LIMIT 1"
    cursor.execute(query, (shortened_url,))
    url_row = cursor.fetchone()
    # Check if short url exists
    if url_row:
      # Update click count
      cursor = conn.cursor()
      query_count = "UPDATE urls SET clicks = clicks + 1 WHERE id = ?"
      cursor.execute(query_count, (url_row['id'],))
      conn.commit()
  except sqlite3.Error as e:
    print(e) # Log error to server only
  finally:
    if conn:
      # Close DB connection
      conn.close()
    # Check if short url exists
    if url_row:
      # Redirect to original URL
      return redirect(url_row['original_url'])
    # If URL doesn't exist, render error page with 404 HTTP Status code
    return render_template('error.html'), 404

# Delete URL route
@app.route('/<shortened_url>/delete')
def delete_url(shortened_url):
  # Check if user is logged in
  if current_user.is_authenticated and current_user.get_id():
    deleted = False
    try:
      # Establish DB connection
      conn = connect_db()
      cursor = conn.cursor()
      # Get the short URL from DB
      query = "SELECT * FROM urls WHERE shortened_url = ? AND user_id = ? LIMIT 1"
      cursor.execute(query, (shortened_url, current_user.get_id()))
      url_row = cursor.fetchone()
      # Check if URL exists
      if url_row:
        # Delete URL from DB
        cursor = conn.cursor()
        query_delete = "DELETE FROM urls WHERE shortened_url = ?"
        cursor.execute(query_delete, (shortened_url,))
        conn.commit()
        deleted = True
    except sqlite3.Error as e:
      print(e) # Log error to server only
      flash("Database error!", "error")
      deleted = False
    finally:
      if conn:
        # Close DB connection
        conn.close()
      if deleted:
        flash("URL " + shortened_url + " successfully deleted!", "info")
      else:
        flash("URL " + shortened_url + " failed to delete. Try again!", "error")
  else:
    # Error message if user is not logged in
    flash("Authentication needed. Please login or register!", "error")
  # Redirect to index regardless of result, with message processed above
  return redirect(url_for('index'))

# Run APP
if __name__ == '__main__':
  # Call Create DB - will create DB for first use
  create_db()
  debug = False
  if os.environ.get('ENVIRONMENT') == 'Development':
    debug = True
  app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=debug)