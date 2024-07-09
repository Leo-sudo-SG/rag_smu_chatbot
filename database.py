import psycopg2

# Initialisierung der Datenbank
def init_db(dbname,user,password,host):
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host
    )
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        token_kmu TEXT PRIMARY KEY,
        email_kmu TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        token_kmu TEXT,
        chat TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS info (
        token_kmu TEXT,
        info TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS kmu_summaries (
        token_kmu TEXT,
        summary TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS interviews (
        token_kmu TEXT,
        token_customer TEXT,
        interview TEXT
    )
    ''')
    conn.commit()
    return conn, c

def connect_db(dbname,user,password,host):
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host
    )
    c = conn.cursor()
    return conn, c

# Funktion zum Registrieren eines neuen Benutzers
def register_user(conn, c, token, email):
    c.execute('INSERT INTO users (token_kmu, email_kmu) VALUES (%s, %s) ON CONFLICT (token_kmu) DO NOTHING', (token, email))
    conn.commit()

# Funktion zum Speichern des Chats in der Datenbank
def save_chat_to_db(conn, c, token, chat):
    c.execute('INSERT INTO chats (token_kmu, chat) VALUES (%s, %s)', (token, chat))
    conn.commit()

def save_info_to_db(conn, c, token, info):
    c.execute('INSERT INTO info (token_kmu, info) VALUES (%s, %s)', (token, info))
    conn.commit()

def save_kmu_summary_to_db(conn, c, token, summary):
    c.execute('INSERT INTO kmu_summaries (token_kmu, summary) VALUES (%s, %s)', (token, summary))
    conn.commit()

def save_interview_to_db(conn, c, token_kmu, token_customer, interview):
    c.execute('INSERT INTO interviews (token_kmu, token_customer, interview) VALUES (%s, %s, %s)', (token_kmu, token_customer, interview))
    conn.commit()

# Funktion zum Laden des Chats aus der Datenbank (noch nicht genutzt)
def load_chat_from_db(c, token):
    c.execute('SELECT chat FROM chats WHERE token_kmu = %s', (token,))
    rows = c.fetchall()
    chats = [row[0] for row in rows]
    return chats

def load_info_from_db(c, token):
    c.execute('SELECT info FROM info WHERE token_kmu = %s', (token,))
    row = c.fetchone()
    return row[0] if row else None

def load_summary_from_db(c, token):
    c.execute('SELECT summary FROM kmu_summaries WHERE token_kmu = %s', (token,))
    row = c.fetchone()
    return row[0] if row else None

def load_email_from_db(c, token):
    c.execute('SELECT email_kmu FROM users WHERE token_kmu = %s', (token,))
    row = c.fetchone()
    return row[0] if row else None
