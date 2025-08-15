import psycopg2
import csv

# ==== CONFIGURATION ====
OLD_DB_URL = ""  # Old DB
NEW_DB_URL = ""  # New DB

USERS_CSV = "users.csv"
WORDS_CSV = "words.csv"

# ==== DB CONNECTION FUNCTION ====
def get_conn(db_url):
    return psycopg2.connect(db_url, sslmode='require')

# ==== STEP 1: EXPORT OLD DB TO CSV ====
def export_to_csv():
    with get_conn(OLD_DB_URL) as conn:
        cur = conn.cursor()

        # Export users table
        cur.execute("SELECT * FROM users;")
        rows = cur.fetchall()
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in cur.description])  # header
            writer.writerows(rows)

        # Export words table
        cur.execute("SELECT * FROM words;")
        rows = cur.fetchall()
        with open(WORDS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in cur.description])  # header
            writer.writerows(rows)

        print(f"✅ Data exported to {USERS_CSV} and {WORDS_CSV}")

# ==== STEP 2: CREATE TABLES IN NEW DB ====
def create_tables():
    with get_conn(NEW_DB_URL) as conn:
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
        conn.commit()
        print("✅ Tables created in new DB")

# ==== STEP 3: IMPORT FROM CSV TO NEW DB ====
def import_from_csv():
    with get_conn(NEW_DB_URL) as conn:
        cur = conn.cursor()

        # Insert into users
        with open(USERS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    INSERT INTO users (id, username, password)
                    VALUES (%s, %s, %s)
                """, (row["id"], row["username"], row["password"]))

        # Insert into words
        with open(WORDS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    INSERT INTO words (id, user_id, word, meaning)
                    VALUES (%s, %s, %s, %s)
                """, (row["id"], row["user_id"], row["word"], row["meaning"]))

        conn.commit()
        print("✅ Data imported into new DB")

# ==== MAIN ====
if __name__ == "__main__":
    # Run below 1st  to take backup
    export_to_csv()
    # After above function complete delete postre sql db and create new and update URL
    # after new db created run below 2 funtions
    # create_tables()
    # import_from_csv()
    print("🎯 Migration complete!")
