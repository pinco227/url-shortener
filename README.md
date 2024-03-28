

# URL Shortener

**URL Shortener** is a web app that helps users convert long URLs into short ones that redirects back to the original ones. This is helpful for sharing URLs as they are short and user-friendly. This project serves as a Mini-Project for **Secure Web Programing** module of **University of Galway's** for **Postgraduate Diploma in Cybersecurity and Software Development.**

## Design & Development
### Flow Diagram

### DB Schema


## Development
### Environment (IDE):
For developing this project I used VSCode IDE. To keep dependencies project-separated, I used python's [`venv`](https://docs.python.org/3/library/venv.html) library using the following commands: `py -m venv path/to/venv` to create the virtual environment, and then `source path/to/venv/Scripts/activate` to activate the virtual env on the current terminal. All packages installed when venv is active are only installed for this project and not globally.
### Packages
To build this project I used the following python packages:
- Flask
- WTForms
- Flask-WTF
- Bcrypt
- Flask-Bcrypt
- Flask-Login
- Jinja2

Other built-in libraries used:
- sqlite3
- datetime
- os
- string
- random

## Deployment
Follow these steps to run this project in your environment:
1. Clone or download this project and open terminal in the project's root
   - `git clone https://github.com/pinco227/url-shortener.git`
   - OR [Download ZIP](https://github.com/pinco227/url-shortener/archive/refs/heads/main.zip)
2. (Optional) Create virtual environment: `python -m venv venv`
   - Activate environment: `source venv/Scripts/activate`
3. Install requirements: `pip install -r requirements.txt`
4. Create [ReCaptcha](https://www.google.com/recaptcha/admin/) site and retrieve keys.
5. Create env.py file and include the following code (note that the values should be replaced with your own credentials)
   ```python
    import os

    # App IP and PORT
    os.environ.setdefault("IP", "localhost")
    os.environ.setdefault("PORT", "5000")
    os.environ.setdefault("ENVIRONMENT", "Development")
    # Generate a secret key, use https://randomkeygen.com/
    os.environ.setdefault("SECRET_KEY", "<secret_key>")
    # Database
    os.environ.setdefault("DATABASE_URL", "url_shortener.db")
    # Recaptcha keys. Go to https://www.google.com/recaptcha/admin/create and
    # create a new site
    os.environ.setdefault(
        "RC_SITE_KEY", "<recaptcha_site_key>")
    os.environ.setdefault(
        "RC_SECRET_KEY", "<recaptcha_secret_key>")
   ```
6. Run application: `python app.py`
   - This will create database file and tables on first run