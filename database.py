import sqlite3

DB_PATH="data/notely.db"

def get_db():
    db=sqlite3.connect(DB_PATH)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init_db():
    db=sqlite3.connect(DB_PATH)
    db.execute("PRAGMA user_version=1")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            profile_picture TEXT,
            created_at INTEGER NOT NULL
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
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
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
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            FOREIGN KEY(blog_id) REFERENCES blogs(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(parent_id) REFERENCES comments(id) ON DELETE CASCADE ON UPDATE CASCADE
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
    db=get_db()
    cur=db.execute(query,args)
    rv=cur.fetchall()
    cur.close()
    db.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query,args=()):
    db=get_db()
    cur=db.execute(query,args)
    db.commit()
    lastrowid=cur.lastrowid
    db.close()
    return lastrowid
