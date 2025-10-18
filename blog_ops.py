from database import query_db,execute_db
from datetime import datetime
from id_generator import generate_id

def create_blog(user_id,title,content,is_draft=1):
    if not title or len(title.strip())==0:
        return None,"Title cannot be empty"
    if len(title)>200:
        return None,"Title must be 200 characters or less"
    if not content or len(content.strip())==0:
        return None,"Content cannot be empty"
    blog_id=generate_id()
    execute_db("INSERT INTO blogs(id,user_id,title,content,is_draft) VALUES(?,?,?,?,?)",(blog_id,user_id,title,content,is_draft))
    return blog_id,None

def update_blog(blog_id,user_id,title,content,is_draft):
    blog=query_db("SELECT user_id FROM blogs WHERE id=?",(blog_id,),one=True)
    if not blog:
        return False,"Blog not found"
    if blog["user_id"]!=user_id:
        return False,"Unauthorized"
    if not title or len(title.strip())==0:
        return False,"Title cannot be empty"
    if len(title)>200:
        return False,"Title must be 200 characters or less"
    if not content or len(content.strip())==0:
        return False,"Content cannot be empty"
    execute_db("UPDATE blogs SET title=?,content=?,is_draft=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(title,content,is_draft,blog_id))
    return True,None

def delete_blog(blog_id,user_id):
    blog=query_db("SELECT user_id FROM blogs WHERE id=?",(blog_id,),one=True)
    if not blog:
        return False,"Blog not found"
    if blog["user_id"]!=user_id:
        return False,"Unauthorized"
    execute_db("DELETE FROM blogs WHERE id=?",(blog_id,))
    return True,None

def get_blog(blog_id):
    blog=query_db("""
        SELECT b.id,b.title,b.content,b.is_draft,b.created_at,b.updated_at,
               u.id as user_id,u.username,u.display_name,u.profile_picture
        FROM blogs b
        JOIN users u ON b.user_id=u.id
        WHERE b.id=?
    """,(blog_id,),one=True)
    return dict(blog) if blog else None

def get_user_blogs(user_id,include_drafts=False,page=1,per_page=10):
    offset=(page-1)*per_page
    if include_drafts:
        blogs=query_db("SELECT id,title,is_draft,created_at,updated_at FROM blogs WHERE user_id=? ORDER BY updated_at DESC LIMIT ? OFFSET ?",(user_id,per_page,offset))
        total=query_db("SELECT COUNT(*) as count FROM blogs WHERE user_id=?",(user_id,),one=True)
    else:
        blogs=query_db("SELECT id,title,created_at,updated_at FROM blogs WHERE user_id=? AND is_draft=0 ORDER BY created_at DESC LIMIT ? OFFSET ?",(user_id,per_page,offset))
        total=query_db("SELECT COUNT(*) as count FROM blogs WHERE user_id=? AND is_draft=0",(user_id,),one=True)
    total_count=total["count"] if total else 0
    total_pages=(total_count+per_page-1)//per_page
    return [dict(blog) for blog in blogs],total_count,total_pages,page

def get_recent_blogs(limit=20):
    blogs=query_db("""
        SELECT b.id,b.title,b.created_at,
               u.username,u.display_name,u.profile_picture
        FROM blogs b
        JOIN users u ON b.user_id=u.id
        WHERE b.is_draft=0
        ORDER BY b.created_at DESC
        LIMIT ?
    """,(limit,))
    return [dict(blog) for blog in blogs]

def search_blogs(query):
    search_term=f"%{query}%"
    blogs=query_db("""
        SELECT b.id,b.title,b.created_at,
               u.username,u.display_name,u.profile_picture
        FROM blogs b
        JOIN users u ON b.user_id=u.id
        WHERE b.is_draft=0 AND (b.title LIKE ? OR b.content LIKE ?)
        ORDER BY b.created_at DESC
    """,(search_term,search_term))
    return [dict(blog) for blog in blogs]

def get_user_by_username(username):
    user=query_db("SELECT id,username,display_name,profile_picture,created_at FROM users WHERE username=?",(username,),one=True)
    return dict(user) if user else None
