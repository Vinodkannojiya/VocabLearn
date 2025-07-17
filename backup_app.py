from flask import Flask, request, redirect, session, render_template_string
from googletrans import Translator
import sqlite3

app = Flask(__name__)
app.secret_key = 'mysecret'

translator = Translator()

# --- Bootstrap Template Base ---
base_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">  <!-- ✅ This line fixes mobile zoom -->
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



# --- Init DB ---
def init_db():
    conn = sqlite3.connect('vocab.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, user_id INTEGER, word TEXT, meaning TEXT)''')
    c.execute('SELECT * FROM users WHERE username=?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'pass123'))
    conn.commit()
    conn.close()

init_db()

# --- Templates ---
def render_with_base(content, title="Vocabulary App"):
    return render_template_string(base_template, content=content, title=title)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        conn = sqlite3.connect('vocab.db')
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username=? AND password=?', (uname, pwd))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['word_index'] = 0
            return redirect('/home')
        else:
            error = "Invalid Credentials"
    else:
        error = None

    form_template = '''
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

    content = render_template_string(form_template, error=error)
    return render_template_string(base_template, content=content, title="Login")


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
    return render_with_base(content, title="Home")


import requests

@app.route('/add_word', methods=['GET', 'POST'])
def add_word():
    if 'user_id' not in session:
        return redirect('/')

    message = None

    if request.method == 'POST':
        word = request.form['word']

        # Translate word to Hindi
        hindi_meaning = translator.translate(word, src='en', dest='hi').text

        # Get example sentences using dictionaryapi.dev
        example_sentences = []
        try:
            res = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
            if res.status_code == 200:
                data = res.json()
                meanings = data[0].get('meanings', [])
                for meaning in meanings:
                    defs = meaning.get('definitions', [])
                    for d in defs:
                        if 'example' in d:
                            example_sentences.append(d['example'])
                        if len(example_sentences) >= 2:
                            break
                    if len(example_sentences) >= 2:
                        break
        except:
            pass

        # Combine Hindi meaning + examples
        full_meaning = hindi_meaning
        if example_sentences:
            full_meaning += "\nExamples:\n" + "\n".join(f"- {e}" for e in example_sentences)

        # Save to DB
        conn = sqlite3.connect('vocab.db')
        c = conn.cursor()
        c.execute('INSERT INTO words (user_id, word, meaning) VALUES (?, ?, ?)',
                  (session['user_id'], word, full_meaning))
        conn.commit()
        conn.close()

        message = f"✅ Word '{word}' added!"

    # Form HTML
    form_template = '''
    <h2>Add Word</h2>
    {% if message %}
        <div class="alert alert-success">{{ message }}</div>
    {% endif %}
    <form method="POST" class="card p-3 shadow-sm">
      <div class="mb-3">
        <label>English Word:</label>
        <input name="word" class="form-control" required>
      </div>
      <button type="submit" class="btn btn-success">Add Word</button>
    </form>
    <a href="/home" class="btn btn-link mt-2">⬅️ Back to Home</a>
    '''

    content = render_template_string(form_template, message=message)
    return render_template_string(base_template, content=content, title="Add Word")


@app.route('/word_history', methods=['GET', 'POST'])
def word_history():
    if 'user_id' not in session:
        return redirect('/')

    conn = sqlite3.connect('vocab.db')
    c = conn.cursor()

    # Handle deletion first
    if request.method == 'POST' and 'delete' in request.form:
        delete_word = request.form['delete']
        c.execute('DELETE FROM words WHERE user_id=? AND word=?', (session['user_id'], delete_word))
        conn.commit()
        message = f"✅ Word '{delete_word}' deleted!"
        session['word_index'] = 0  # reset to beginning
    else:
        message = None

    # Fetch updated word list
    c.execute('SELECT word, meaning FROM words WHERE user_id=?', (session['user_id'],))
    word_list = c.fetchall()
    conn.close()

    if not word_list:
        return render_with_base("<p>No words added yet.</p><a href='/home'>⬅️ Back to Home</a>")

    index = session.get('word_index', 0)
    if index >= len(word_list):
        index = 0
        session['word_index'] = 0

    show_meaning = False
    if request.method == 'POST':
        if 'next' in request.form:
            index = (index + 1) % len(word_list)
            session['word_index'] = index
        elif 'meaning' in request.form:
            show_meaning = True

    word, meaning = word_list[index]
    formatted_meaning = meaning.replace("\n", "<br>")  # ✅ SAFE for Python 3.11+

    content = f'''
    <h2>Word History</h2>
    {'<div class="alert alert-success">' + message + '</div>' if message else ''}
    <div class="card p-3 shadow-sm">
        <p><b>Word:</b> {word}</p>
        {"<p><b>Meaning:</b><br>" + formatted_meaning + "</p>" if show_meaning else ""}
        <form method="POST" class="d-flex gap-2 flex-wrap">
            <button name="meaning" type="submit" class="btn btn-info">Get Meaning</button>
            <button name="next" type="submit" class="btn btn-secondary">Next</button>
            <button name="delete" value="{word}" onclick="return confirm('Are you sure?')" class="btn btn-danger">Delete</button>
        </form>
    </div>
    <a href="/home" class="btn btn-link mt-2">⬅️ Back to Home</a>
    '''
    return render_with_base(content)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False)
