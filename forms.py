from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.recaptcha.validators import Recaptcha
from wtforms import EmailField, StringField, SubmitField, PasswordField, TelField, URLField, SearchField, ValidationError
from wtforms.validators import DataRequired, Email, URL, EqualTo, Length, Optional

# Custom password validator
def complex_password(form, field):
  password = field.data
  if not any(char.isupper() for char in password):
    raise ValidationError('Password must contain an uppercase letter.')
  if not any(char.islower() for char in password):
    raise ValidationError('Password must contain a lowercase letter.')
  if not any(char.isdigit() for char in password):
    raise ValidationError('Password must contain a number.')
  if not any(char in '!@#$%^&*(' for char in password):
    raise ValidationError('Password must contain a symbol.')

class LoginForm(FlaskForm):
  class Meta:
    csrf = True
  """Login Form"""
  username = StringField('Username', validators=[
      DataRequired(message='Please enter Username!')])
  password = PasswordField('Password', validators=[
      DataRequired(message='Please enter Password!')])
  submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
  class Meta:
    csrf = True
  """Login Form"""
  username = StringField('Username', validators=[
      DataRequired(message='Please enter Username!'),
      Length(max=50, min=3, message='Username must be between %(min)d and %(max)d characters long.')])
  email = EmailField('Email Address', validators=[
      DataRequired(message='Please fill in your email address!'),
      Email(message='Invalid email address!'),
      Length(max=320, min=6, message='Email must be between %(min)d and %(max)d characters long.')])
  fname = StringField('First Name', validators=[
      DataRequired(message='Please enter First Name!'),
      Length(max=35, min=2, message='First Name must be between %(min)d and %(max)d characters long.')])
  lname = StringField('Last Name', validators=[
      DataRequired(message='Please enter Last Name!'),
      Length(max=35, min=2, message='Last Name must be between %(min)d and %(max)d characters long.')])
  phone = TelField('Phone Number', validators=[
      Optional(),
      Length(max=35, min=2, message='Last Name must be between %(min)d and %(max)d characters long.')])
  website = URLField('Website URL', validators=[
      Optional(),
      URL(message='Invalid URL!'),
      Length(min=10, message='URL must be between %(min)d characters minimum.')])
  password = PasswordField('Password', validators=[
      DataRequired(message='Please enter Password!'),
      Length(min=8, message='Password must be at least %(min)d characters long.'),
      complex_password])
  repeat_password = PasswordField('Confirm Password', validators=[
      DataRequired(message='Please enter Password!'),
      EqualTo('password', message='Passwords must match.')])
  recaptcha = RecaptchaField(
      validators=[Recaptcha(message='Please check the security Recaptcha field!')])
  submit = SubmitField('Sign Up')
  
class ProfileForm(FlaskForm):
  class Meta:
    csrf = True
  """Profile Edit Form"""
  email = EmailField('Email Address', validators=[
      DataRequired(message='Please fill in your email address!'),
      Email(message='Invalid email address!')])
  fname = StringField('First Name', validators=[
      DataRequired(message='Please enter First Name!')])
  lname = StringField('Last Name', validators=[
      DataRequired(message='Please enter Last Name!')])
  phone = TelField('Phone Number')
  website = URLField('Website URL', validators=[
      URL(message='Invalid URL!')])
  recaptcha = RecaptchaField(
      validators=[Recaptcha(message='Please check the security Recaptcha field!')])
  submit = SubmitField('Update')

class CreateURLForm(FlaskForm):
  class Meta:
    csrf = True
  """Create URL Form"""
  original_url = URLField('Enter your original URL', validators=[
      URL(message='Invalid URL!')])
  recaptcha = RecaptchaField(
      validators=[Recaptcha(message='Please check the security Recaptcha field!')])
  submit = SubmitField('Create')
  
class SearchForm(FlaskForm):
  class Meta:
    csrf = False
  """Create URL Form"""
  q = SearchField('Search for URLs', validators=[
    Length(max=50, min=2, message='Search term must be between %(min)d and %(max)d characters long!'),
    DataRequired(message='Please enter search term!')])