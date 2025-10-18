import sqlite3
import os
from datetime import datetime
from flask import g,current_app

def get_db():
    if "db" not in g:
        g.db=sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory=sqlite3.Row
    return g.db

def close_db(e=None):
    db=g.pop("db",None)
    if db is not None:
        db.close()

def init_db():
    db=sqlite3.connect("notely.db")
    db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            profile_picture TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS sessions(
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            browser TEXT,
            device TEXT,
            created_at INTEGER NOT NULL,
            last_active INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS blogs(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            is_draft INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS comments(
            id TEXT PRIMARY KEY,
            blog_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            parent_id TEXT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(blog_id) REFERENCES blogs(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(parent_id) REFERENCES comments(id) ON DELETE CASCADE
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_blogs_user ON blogs(user_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_blogs_draft ON blogs(is_draft)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_comments_blog ON comments(blog_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id)")
    db.commit()
    db.close()

def query_db(query,args=(),one=False):
    cur=get_db().execute(query,args)
    rv=cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query,args=()):
    db=get_db()
    cur=db.execute(query,args)
    db.commit()
    return cur.lastrowid
