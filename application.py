import os
import requests

from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    if session["current_user"] == []:
        flash("Please register or login to access contents of this website.")
    return render_template("main.html", user=session["current_user"])

@app.route("/register", methods=["GET", "POST"])
def signup():
    session["current_user"] = []

    if request.method == "POST":
        username = request.form.get("user")
        password = request.form.get("pass")

        if db.execute("SELECT * FROM public.user WHERE username = :username", {"username": username}).rowcount != 0:
            flash('Whoops! This username is already taken!')

        else:
            db.execute("INSERT INTO public.user (username, password) VALUES (:username, :password)", {"username": username, "password": password})
            db.commit()
            return redirect(url_for('login'))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("current_user") is None:
        session["current_user"] = []
    if request.method == "POST":
        username = request.form.get("user")
        password = request.form.get("pass")

        if db.execute("SELECT * FROM public.user WHERE username = :username AND password = :password", {"username": username, "password": password}).rowcount == 0:
            flash('Invalid credentials')

        else:
            session["current_user"] = username
            return redirect(url_for('index'))

    return render_template("sign-in.html")

@app.route("/logout")
def logout():
    session["current_user"] = []
    return redirect(url_for('index'))

@app.route("/search", methods=["GET"])
def search():
    search = request.args["keywords"]
    if search == "":
        return redirect(url_for('index'))
    else:
        result = db.execute("SELECT * from public.book WHERE (isbn LIKE :search) OR (title LIKE :search) OR (author LIKE :search)", {"search": '%' + search + '%'})

        flash(f"{result.rowcount} match(es) found for '{search}'")

        return render_template("search.html", result=result, user=session["current_user"])
