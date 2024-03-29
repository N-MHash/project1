import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

file = open("books.csv")
reader = csv.reader(file)

for isbn, title, author, year in reader:
    db.execute("INSERT INTO book (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
    print(f"Added <{title}> book info with ISBN #{isbn}")

db.commit()
