from flask import Flask, request, redirect, session, render_template_string
import psycopg2
import os
import requests
from googletrans import Translator

app = Flask(__name__)
app.secret_key = 'mysecret'
translator = Translator()

# --- PostgreSQL Config ---
DATABASE_URL = os.environ["DATABASE_INTERNAL_URL"]
# add below value during local testing
# DATABASE_URL = "NEED TO UDASET FROM RENDER"


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            );
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                word TEXT,
                meaning TEXT
            );
        ''')
        users = [
            ('admin', 'pass123'),
            ('vinod', 'pass123'),
            ('pramod', 'pass123'),
            ('manoj', 'pass123'),
            ('hemlata', 'pass123'),
            ('sangita', 'pass123'),
            ('devraj', 'pass123'),
            ('kunal', 'pass123'),
            ('sonakshi', 'pass123'),
            ('samar', 'pass123'),
            ('arya', 'pass123'),
            ('janvi', 'pass123'),
            ('neel', 'pass123'),
            ('user', 'pass123')
        ]

        cur.execute("SELECT id FROM users WHERE username='admin'")
        if not cur.fetchone():
            cur.executemany("INSERT INTO users (username, password) VALUES (%s, %s)", users)
        conn.commit()


init_db()

# --- Base Template ---
base_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background: linear-gradient(to right, #e3f2fd, #ffffff);
      font-family: 'Segoe UI', sans-serif;
    }
    .btn-rounded {
      border-radius: 25px;
      padding-left: 20px;
      padding-right: 20px;
    }
    .card {
      border: none;
      border-radius: 20px;
    }
    .card-title {
      color: #1976d2;
    }
    .banner {
      background: linear-gradient(to right, #42a5f5, #1e88e5);
      color: white;
      padding: 2rem;
      border-radius: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      margin-bottom: 2rem;
    }
  </style>
</head>
<body class="bg-light">
  <div class="container py-4">
    {{ content | safe }}
  </div>
</body>
</html>
'''


def render_with_base(content, title="Vocabulary App"):
    return render_template_string(base_template, content=content, title=title)


@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (uname, pwd))
            user = cur.fetchone()
            if user:
                session['user_id'] = user[0]
                session['word_index'] = 0
                return redirect('/home')
            else:
                error = "Invalid Credentials"

    form = '''
    <h2 class="text-center">Login</h2>
    <form method="POST" class="card p-3 shadow">
      <div class="mb-3">
        <label>Username:</label>
        <input name="username" class="form-control" required>
      </div>
      <div class="mb-3">
        <label>Password:</label>
        <input name="password" type="password" class="form-control" required>
      </div>
      <button type="submit" class="btn btn-primary">Login</button>
    </form>
    {% if error %}
    <p class="text-danger mt-2">{{ error }}</p>
    {% endif %}
    '''
    return render_template_string(base_template, content=render_template_string(form, error=error), title="Login")


@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/')
    content = '''
    <div class="banner text-center">
        <h1>🧠 Grow Your Vocabulary</h1>
        <p>Learn new words daily, test yourself, and become a word wizard!</p>
    </div>
    <div class="row text-center">
        <div class="col-md-4 mb-3">
            <a href="/add_word" class="btn btn-success btn-lg btn-rounded w-100 shadow">➕ Add New Word</a>
        </div>
        <div class="col-md-4 mb-3">
            <a href="/word_history" class="btn btn-primary btn-lg btn-rounded w-100 shadow">📖 Word History</a>
        </div>
        <div class="col-md-4 mb-3">
            <a href="/logout" class="btn btn-danger btn-lg btn-rounded w-100 shadow">🚪 Logout</a>
        </div>
    </div>
    '''
    return render_with_base(content, "Home")


@app.route('/add_word', methods=['GET', 'POST'])
def add_word():
    if 'user_id' not in session:
        return redirect('/')

    message = None
    if request.method == 'POST':
        words = request.form.getlist('word[]')

        with get_conn() as conn:
            cur = conn.cursor()

            for word in words:
                word = word.strip()
                if not word:
                    continue

                # Auto-translate and get examples
                hindi_meaning = translator.translate(word, src='en', dest='hi').text
                example_sentences = []
                try:
                    res = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
                    if res.status_code == 200:
                        for meaning_data in res.json()[0].get('meanings', []):
                            for d in meaning_data.get('definitions', []):
                                if 'example' in d:
                                    example_sentences.append(d['example'])
                                if len(example_sentences) >= 2:
                                    break
                            if len(example_sentences) >= 2:
                                break
                except:
                    pass

                full_meaning = hindi_meaning
                if example_sentences:
                    full_meaning += "\nExamples:\n" + "\n".join(f"- {e}" for e in example_sentences)

                cur.execute(
                    "INSERT INTO words (user_id, word, meaning) VALUES (%s, %s, %s)",
                    (session['user_id'], word, full_meaning)
                )

            conn.commit()
            message = f"✅ {len(words)} word(s) added!"

    form = '''
    <h2 class="text-center mb-4" style="font-family:'Poppins',sans-serif; font-weight:600;">Add Words</h2>
    {% if message %}
        <div class="alert alert-success">{{ message }}</div>
    {% endif %}
    <form method="POST" class="card p-3 shadow-sm" id="addWordsForm">
        <div id="wordFields">
            <div class="word-row mb-2 d-flex">
                <input type="text" name="word[]" class="form-control me-2" placeholder="English Word" required>
                <button type="button" class="btn btn-success add-btn">+</button>
            </div>
        </div>
        <div class="mt-3 d-flex justify-content-center gap-3">
            <button type="submit" class="btn btn-outline-primary btn-rounded px-4">SAVE WORDS</button>
            <a href="/home" class="btn btn-outline-success btn-rounded px-4">HOME</a>
        </div>
    </form>

    <script>
    document.addEventListener("DOMContentLoaded", function() {
        const wordFields = document.getElementById("wordFields");

        wordFields.addEventListener("click", function(e) {
            if (e.target.classList.contains("add-btn")) {
                e.preventDefault();
                const newRow = document.createElement("div");
                newRow.classList.add("word-row", "mb-2", "d-flex");
                newRow.innerHTML = `
                    <input type="text" name="word[]" class="form-control me-2" placeholder="English Word" required>
                    <button type="button" class="btn btn-danger remove-btn">-</button>
                `;
                wordFields.appendChild(newRow);
            } else if (e.target.classList.contains("remove-btn")) {
                e.preventDefault();
                e.target.closest(".word-row").remove();
            }
        });
    });
    </script>
    '''
    return render_template_string(base_template, content=render_template_string(form, message=message),
                                  title="Add Words")





@app.route('/word_history')
def word_history():
    if 'user_id' not in session:
        return redirect('/')

    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    with get_conn() as conn:
        cur = conn.cursor()

        # Count total words
        cur.execute("SELECT COUNT(*) FROM words WHERE user_id=%s", (session['user_id'],))
        total_words = cur.fetchone()[0]

        # Fetch paginated words
        cur.execute("""
            SELECT word, meaning FROM words
            WHERE user_id=%s
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (session['user_id'], per_page, offset))
        words = cur.fetchall()

    total_pages = (total_words + per_page - 1) // per_page

    # Bootstrap bright colors
    colors = [
        "primary", "success", "danger", "warning", "info",
        "secondary", "dark"
    ]

    # Generate HTML blocks
    word_blocks = ""
    for idx, (w, m) in enumerate(words, start=1):
        color_class = colors[(idx - 1) % len(colors)]
        formatted_meaning = m.replace("\n", "<br>")

        word_blocks += f"""
        <div class="mb-3">
            <button class="btn btn-{color_class} w-100 text-start" 
                    style="border-radius: 25px; font-family: 'Poppins', sans-serif; 
                           font-size: 1.15rem; font-weight: 600; padding: 12px 16px; 
                           text-transform: capitalize;"
                    onclick="toggleMeaning('meaning_{idx}')">
                {idx}. {w}
            </button>
            <div id="meaning_{idx}" 
                 class="p-3 mt-1 rounded text-white" 
                 style="display:none; background-color: var(--bs-{color_class}-rgb, var(--bs-{color_class})); 
                        background-color: rgba(var(--bs-{color_class}-rgb), 0.85); 
                        font-size: 1rem; font-weight: 500;">
                {formatted_meaning}
            </div>
        </div>
        """

    # Navigation buttons
    pagination_html = '<div class="d-flex justify-content-between mt-4">'
    if page > 1:
        pagination_html += f'<a href="?page={page - 1}" class="btn btn-outline-primary btn-rounded px-4">⬅ PREV</a>'
    else:
        pagination_html += '<span></span>'
    pagination_html += '<a href="/home" class="btn btn-outline-success btn-rounded px-4">HOME</a>'
    if page < total_pages:
        pagination_html += f'<a href="?page={page + 1}" class="btn btn-outline-primary btn-rounded px-4">NEXT ➡</a>'
    pagination_html += '</div>'

    # JS toggle
    js_script = """
    <script>
    function toggleMeaning(id) {
        var el = document.getElementById(id);
        if (el.style.display === "none") {
            el.style.display = "block";
        } else {
            el.style.display = "none";
        }
    }
    </script>
    """

    content = f"""
    <h2 class="text-center mb-4" style="font-family:'Poppins',sans-serif; font-weight:600;">Word History</h2>
    {word_blocks}
    {pagination_html}
    {js_script}
    """

    return render_with_base(content, "Word History")


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=False)
