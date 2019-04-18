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
    if session.get("current_user") == None or session["current_user"] == []:
        session["current_user"] = []
        flash("Please register or login to access contents of this website.")
    return render_template("main.html", user=session.get('current_user'))

@app.route("/register", methods=["GET", "POST"])
def signup():
    session["current_user"] = []

    if request.method == "POST":
        username = request.form.get("user")
        password = request.form.get("pass")

        # Can someone bypass this to create duplicate usernames?
        if db.execute("SELECT * FROM public.user WHERE username = :username LIMIT 1", {"username": username}).rowcount != 0:
            flash('Whoops! This username is already taken!')

        else:
            db.execute("INSERT INTO public.user (username, password) VALUES (:username, :password)", {"username": username, "password": password})
            db.commit()
            flash("You've successfully created an account.")
            return redirect(url_for('index'))

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
    if session.get("current_user") == []:
        return redirect(url_for('index'))
    else:
        search = request.args["keywords"]
        if search == "":
            return redirect(url_for('index'))
        else:
            result = db.execute("SELECT * FROM public.book WHERE (isbn LIKE :search) OR (title LIKE :search) OR (author LIKE :search)", {"search": '%' + search + '%'})

            flash(f"{result.rowcount} match(es) found for '{search}'")

            return render_template("search.html", result=result, user=session["current_user"])

@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    # Fetch session user's ID
    user_id = db.execute("SELECT id FROM public.user WHERE username = :username", {"username": session["current_user"]}).fetchone()[0]

    # Fetch book info
    book = db.execute("SELECT * FROM public.book WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        flash("This book doesn't exist in our database")
        return redirect(url_for('index'))

    # Display user reviews
    # reviews = db.execute("SELECT * FROM public.user_book_review WHERE book_isbn = :isbn", {"isbn": isbn})
    reviews = db.execute("SELECT username, review_comment, review_rating FROM public.user FULL OUTER JOIN public.user_book_review ON public.user.id = public.user_book_review.username_id WHERE book_isbn = :isbn", {"isbn": isbn})
#    reviewer = db.execute("SELECT username FROM public.user WHERE id = :user_id", {"user_id": reviews.username_id})

    # Check if current user already reviewed the book
    cur = db.execute("SELECT * FROM public.user_book_review WHERE (username_id = :user_id) AND (book_isbn = :isbn)", {"user_id": user_id, "isbn": isbn})

    if cur.rowcount > 0:
        reviewed = True
        rating = cur.fetchone()[3]

    else:
        reviewed = False
        rating = None

    # Submit review
    if request.method == "POST":
        review_rating = int(request.form.get("review_rating"))
        review_comment = request.form.get("review_comment")

        # Server-side check for review rating
        if review_rating > 5 or review_rating < 1:
            flash("An error occurred. Please try again.")
            return redirect(url_for('book', isbn=isbn))

        if db.execute("SELECT * FROM public.user_book_review WHERE (username_id = :user_id) AND (book_isbn = :isbn)", {"user_id": user_id, "isbn": isbn}).rowcount > 0:
            flash("It seems you've already reviewed this book.")

        else:
            db.execute("INSERT INTO public.user_book_review (username_id, book_isbn, review_comment, review_rating) VALUES (:user_id, :book_isbn, :review_comment, :review_rating)", {"user_id": user_id, "book_isbn": isbn, "review_comment": review_comment, "review_rating": review_rating})

            db.commit()

            flash("Review added successfully")
            return redirect(url_for('book', isbn=isbn))

    return render_template("book.html", book=book, reviewed=reviewed, rating=rating, reviews=reviews)
