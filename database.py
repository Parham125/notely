import sqlite3
import os

DB_PATH="data/notely.db"
MIGRATIONS_DIR="migrations"

def get_db():
    db=sqlite3.connect(DB_PATH)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    return db

def get_db_version():
    db=sqlite3.connect(DB_PATH)
    cursor=db.cursor()
    cursor.execute("PRAGMA user_version")
    version=cursor.fetchone()[0]
    cursor.close()
    db.close()
    return version

def set_db_version(version):
    db=sqlite3.connect(DB_PATH)
    db.execute(f"PRAGMA user_version={version}")
    db.commit()
    db.close()

def run_migration(migration_file):
    migration_path=os.path.join(MIGRATIONS_DIR,migration_file)
    if not os.path.exists(migration_path):
        raise FileNotFoundError(f"Migration file {migration_file} not found")
    with open(migration_path,'r') as f:
        migration_sql=f.read()
    db=sqlite3.connect(DB_PATH)
    db.executescript(migration_sql)
    db.commit()
    db.close()

def run_migrations():
    current_version=get_db_version()
    if os.path.exists(MIGRATIONS_DIR):
        migration_files=[]
        for file in os.listdir(MIGRATIONS_DIR):
            if file.endswith('.sql') and file.replace('.sql','').isdigit():
                migration_files.append(int(file.replace('.sql','')))
        migration_files.sort()  # Sort numerically since we converted to int
        for version in migration_files:
            if version>current_version:
                run_migration(f"{version}.sql")
                current_version=version
    return current_version

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    db_exists=os.path.exists(DB_PATH)

    db=sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")

    if db_exists:
        run_migrations()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            profile_picture TEXT,
            role TEXT DEFAULT 'user',
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
    db.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    db.commit()
    db.close()

    if not db_exists:
        set_db_version(2)

def get_admin_count():
    result=query_db("SELECT COUNT(*) as count FROM users WHERE role='admin'",one=True)
    return result['count'] if result else 0

def ensure_at_least_one_admin():
    if get_admin_count()==0:
        first_user=query_db("SELECT id FROM users ORDER BY created_at LIMIT 1",one=True)
        if first_user:
            execute_db("UPDATE users SET role='admin' WHERE id=?",(first_user['id'],))
            return True
    return False

def update_user_role(user_id,role):
    if role!='admin' and get_admin_count()<=1 and get_user_role(user_id)=='admin':
        return False
    execute_db("UPDATE users SET role=? WHERE id=?",(role,user_id))
    return True

def get_user_role(user_id):
    result=query_db("SELECT role FROM users WHERE id=?",(user_id,),one=True)
    return result['role'] if result else 'user'

def get_all_users(limit=50,offset=0,search=None):
    query="SELECT id,username,display_name,role,created_at FROM users"
    args=[]
    if search:
        query+=" WHERE username LIKE ? OR display_name LIKE ?"
        args.extend([f"%{search}%",f"%{search}%"])
    query+=" ORDER BY created_at DESC LIMIT ? OFFSET ?"
    args.extend([limit,offset])
    return query_db(query,args)

def get_user_stats():
    total_users=query_db("SELECT COUNT(*) as count FROM users",one=True)['count']
    total_blogs=query_db("SELECT COUNT(*) as count FROM blogs",one=True)['count']
    total_comments=query_db("SELECT COUNT(*) as count FROM comments",one=True)['count']
    admin_count=query_db("SELECT COUNT(*) as count FROM users WHERE role='admin'",one=True)['count']
    return {
        'total_users':total_users,
        'total_blogs':total_blogs,
        'total_comments':total_comments,
        'admin_count':admin_count
    }

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
