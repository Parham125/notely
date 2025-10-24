import bcrypt
import time
import threading
from database import query_db,execute_db,get_user_role,update_user_role
from id_generator import generate_id,generate_session_token

role_lock=threading.Lock()

def parse_user_agent(user_agent):
    ua=user_agent.lower()
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device="Mobile"
    elif "tablet" in ua or "ipad" in ua:
        device="Tablet"
    else:
        device="Desktop"
    if "chrome" in ua and "edg" not in ua:
        browser="Chrome"
    elif "firefox" in ua:
        browser="Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser="Safari"
    elif "edg" in ua:
        browser="Edge"
    elif "opera" in ua or "opr" in ua:
        browser="Opera"
    else:
        browser="Unknown"
    return browser,device

def create_session(user_id,user_agent):
    token=generate_session_token()
    browser,device=parse_user_agent(user_agent)
    created_at=int(time.time())
    execute_db("INSERT INTO sessions(token,user_id,browser,device,created_at,last_active) VALUES(?,?,?,?,?,?)",(token,user_id,browser,device,created_at,created_at))
    return token

def get_session(token):
    if not token:
        return None
    session=query_db("SELECT token,user_id,browser,device,created_at,last_active FROM sessions WHERE token=?",(token,),one=True)
    if not session:
        return None
    current_time=int(time.time())
    if current_time-session["last_active"]>2592000:
        delete_session(token)
        return None
    execute_db("UPDATE sessions SET last_active=? WHERE token=?",(current_time,token))
    return dict(session)

def delete_session(token):
    execute_db("DELETE FROM sessions WHERE token=?",(token,))

def delete_session_by_id(token,user_id):
    session=query_db("SELECT user_id FROM sessions WHERE token=?",(token,),one=True)
    if not session or session["user_id"]!=user_id:
        return False
    delete_session(token)
    return True

def get_user_sessions(user_id):
    sessions=query_db("SELECT token,browser,device,created_at,last_active FROM sessions WHERE user_id=? ORDER BY last_active DESC",(user_id,))
    return [dict(s) for s in sessions]

def get_current_user(request):
    token=request.cookies.get("session_token")
    session=get_session(token)
    if not session:
        return None
    user=query_db("SELECT id,username,display_name,profile_picture,role FROM users WHERE id=?",(session["user_id"],),one=True)
    return dict(user) if user else None

def is_admin(user):
    return user and user.get('role')=='admin'

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args,**kwargs):
        from flask import request,redirect,url_for,session
        user=get_current_user(request)
        if not user or not is_admin(user):
            return redirect(url_for('home'))
        return f(*args,**kwargs)
    return decorated_function

def promote_user_to_admin(promoter_id,user_id):
    promoter_role=get_user_role(promoter_id)
    if promoter_role!='admin':
        return False,"Only admins can promote users"

    role_lock.acquire()
    try:
        current_role=get_user_role(user_id)
        if current_role=='admin':
            return False,"User is already an admin"

        user=query_db("SELECT username FROM users WHERE id=?",(user_id,),one=True)
        if not user:
            return False,"User not found"

        if update_user_role(user_id,'admin'):
            return True,f"User {user['username']} promoted to admin"
        return False,"Failed to promote user"
    finally:
        role_lock.release()

def demote_admin_to_user(demoter_id,user_id):
    demoter_role=get_user_role(demoter_id)
    if demoter_role!='admin':
        return False,"Only admins can demote users"

    role_lock.acquire()
    try:
        current_role=get_user_role(user_id)
        if current_role!='admin':
            return False,"User is not an admin"

        admin_count=query_db("SELECT COUNT(*) as count FROM users WHERE role='admin'",one=True)['count']
        if admin_count<=1:
            return False,"Cannot demote the last admin"

        user=query_db("SELECT username FROM users WHERE id=?",(user_id,),one=True)
        if not user:
            return False,"User not found"

        if update_user_role(user_id,'user'):
            return True,f"Admin {user['username']} demoted to user"
        return False,"Failed to demote admin"
    finally:
        role_lock.release()

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt()).decode("utf-8")

def verify_password(password,password_hash):
    return bcrypt.checkpw(password.encode("utf-8"),password_hash.encode("utf-8"))

def register_user(username,display_name,password):
    if query_db("SELECT id FROM users WHERE username=?",(username,),one=True):
        return None,"Username already exists"
    if len(username)<3 or len(username)>20:
        return None,"Username must be 3-20 characters"
    if len(display_name)<1 or len(display_name)>50:
        return None,"Display name must be 1-50 characters"
    if len(password)<6:
        return None,"Password must be at least 6 characters"
    password_hash=hash_password(password)
    user_id=generate_id()
    created_at=int(time.time())
    user_count=query_db("SELECT COUNT(*) as count FROM users",one=True)['count']
    role='admin' if user_count==0 else 'user'
    execute_db("INSERT INTO users(id,username,display_name,password_hash,role,created_at) VALUES(?,?,?,?,?,?)",(user_id,username,display_name,password_hash,role,created_at))
    return user_id,None

def login_user(username,password,user_agent):
    user=query_db("SELECT id,password_hash FROM users WHERE username=?",(username,),one=True)
    if not user or not verify_password(password,user["password_hash"]):
        return None,"Invalid username or password"
    return create_session(user["id"],user_agent),None

def update_profile_picture(user_id,picture_path):
    execute_db("UPDATE users SET profile_picture=? WHERE id=?",(picture_path,user_id))

def delete_user(user_id):
    execute_db("DELETE FROM users WHERE id=?",(user_id,))
