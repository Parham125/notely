from database import query_db,execute_db
from id_generator import generate_id

def create_comment(blog_id,user_id,content,parent_id=None):
    if not content or len(content.strip())==0:
        return None,"Comment cannot be empty"
    if len(content)>1000:
        return None,"Comment must be 1000 characters or less"
    if parent_id:
        parent=query_db("SELECT id,blog_id FROM comments WHERE id=?",(parent_id,),one=True)
        if not parent or parent["blog_id"]!=blog_id:
            return None,"Invalid parent comment"
    comment_id=generate_id()
    execute_db("INSERT INTO comments(id,blog_id,user_id,content,parent_id) VALUES(?,?,?,?,?)",(comment_id,blog_id,user_id,content,parent_id))
    return comment_id,None

def update_comment(comment_id,user_id,content):
    comment=query_db("SELECT user_id FROM comments WHERE id=?",(comment_id,),one=True)
    if not comment:
        return False,"Comment not found"
    if comment["user_id"]!=user_id:
        return False,"Unauthorized"
    if not content or len(content.strip())==0:
        return False,"Comment cannot be empty"
    if len(content)>1000:
        return False,"Comment must be 1000 characters or less"
    execute_db("UPDATE comments SET content=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(content,comment_id))
    return True,None

def delete_comment(comment_id,user_id):
    comment=query_db("SELECT user_id FROM comments WHERE id=?",(comment_id,),one=True)
    if not comment:
        return False,"Comment not found"
    if comment["user_id"]!=user_id:
        return False,"Unauthorized"
    execute_db("DELETE FROM comments WHERE id=?",(comment_id,))
    return True,None

def get_blog_comments(blog_id):
    comments=query_db("""
        SELECT c.id,c.content,c.parent_id,c.created_at,c.updated_at,
               u.id as user_id,u.username,u.display_name,u.profile_picture
        FROM comments c
        JOIN users u ON c.user_id=u.id
        WHERE c.blog_id=?
        ORDER BY c.created_at ASC
    """,(blog_id,))
    return [dict(comment) for comment in comments]

def build_comment_tree(comments):
    comment_map={}
    root_comments=[]
    for comment in comments:
        comment["replies"]=[]
        comment_map[comment["id"]]=comment
    for comment in comments:
        if comment["parent_id"] is None:
            root_comments.append(comment)
        else:
            parent=comment_map.get(comment["parent_id"])
            if parent:
                parent["replies"].append(comment)
    return root_comments
