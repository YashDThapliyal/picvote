import sqlite3
import streamlit as st

DATABASE_NAME = 'picture_voting.db'

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  host_id INTEGER,
                  FOREIGN KEY (host_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  name TEXT NOT NULL,
                  data BLOB NOT NULL,
                  FOREIGN KEY (session_id) REFERENCES sessions(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS votes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  image_id INTEGER,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (image_id) REFERENCES images(id))''')
    
    conn.commit()
    conn.close()

@st.cache_resource
def get_db_connection():
    return sqlite3.connect(DATABASE_NAME, check_same_thread=False)
