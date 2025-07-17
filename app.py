from flask import Flask, render_template, request, redirect
import psycopg2
import os
from urllib.parse import urlparse

app = Flask(__name__)

# ============================
# DATABASE CONNECTION SETUP
# ============================
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment variables.")

url = urlparse(DATABASE_URL)

conn = psycopg2.connect(
    dbname=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

# ============================
# CREATE TABLE IF NOT EXISTS
# ============================
with conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id SERIAL PRIMARY KEY,
                word TEXT NOT NULL,
                meaning TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# ============================
# HOME ROUTE
# ============================
@app.route("/")
def home():
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, word FROM words ORDER BY created_at DESC")
            words = cur.fetchall()
    return render_template("index.html", words=words)


# ============================
# ADD WORD
# ============================
@app.route("/add", methods=["POST"])
def add_word():
    word = request.form.get("word")
    meaning = request.form.get("meaning")

    if word and meaning:
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO words (word, meaning) VALUES (%s, %s)", (word, meaning))
        return redirect("/")
    else:
        return "Missing word or meaning", 400


# ============================
# GET MEANING BY WORD ID
# ============================
@app.route("/meaning/<int:word_id>")
def get_meaning(word_id):
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT meaning FROM words WHERE id = %s", (word_id,))
            result = cur.fetchone()
    if result:
        return result[0]
    return "Not found", 404


# ============================
# DELETE WORD
# ============================
@app.route("/delete/<int:word_id>")
def delete_word(word_id):
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM words WHERE id = %s", (word_id,))
    return redirect("/")


# ============================
# RUN APP
# ============================
if __name__ == "__main__":
    app.run(debug=True)
