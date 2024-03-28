from flask_login import UserMixin

# User Model
class User(UserMixin):
  def __init__(self, id, username, password, fname, lname, email, phone, website):
    self.id = id
    self.username = username
    self.password = password
    self.fname = fname
    self.lname = lname
    self.email = email
    self.phone = phone
    self.website = website
