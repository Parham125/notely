from flask import request,render_template,redirect,url_for,make_response,jsonify,send_from_directory
from datetime import datetime
from waitress import serve
import os
import time
from config import create_app
from database import init_db,execute_db,get_all_users,get_user_stats,get_db_version
from auth import get_current_user,register_user,login_user,delete_session,delete_session_by_id,get_user_sessions,create_session,update_profile_picture,delete_user,require_admin,promote_user_to_admin,demote_admin_to_user,is_admin
from blog_ops import get_recent_blogs,create_blog,get_blog,update_blog,delete_blog,get_user_blogs,search_blogs,get_user_by_username
from comment_ops import create_comment,delete_comment,get_blog_comments,build_comment_tree
from file_handler import save_profile_picture,save_blog_image
from avatar_generator import get_avatar_url
from rate_limiter import check_ip_rate_limit,check_user_rate_limit
import re

def truncate_text(text,max_length=200):
    if len(text)<=max_length:
        return text
    return text[:max_length-3].strip()+"..."

def clean_markdown_for_og(text,max_length=200):
    text=text.strip()
    text=re.sub(r'!\[([^\]]*)\]\([^)]+\)','',text)
    text=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',text)
    text=re.sub(r'#+','',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'\1',text)
    text=re.sub(r'\*([^*]+)\*',r'\1',text)
    text=re.sub(r'__([^_]+)__',r'\1',text)
    text=re.sub(r'_([^_]+)_',r'\1',text)
    text=re.sub(r'`([^`]+)`',r'\1',text)
    text=re.sub(r'~~([^~]+)~~',r'\1',text)
    text=re.sub(r'==([^=]+)==',r'\1',text)
    text=re.sub(r'^\s*[-*+]\s+','',text,flags=re.MULTILINE)
    text=re.sub(r'^\s*\d+\.\s+','',text,flags=re.MULTILINE)
    text=re.sub(r'^\s*>\s*','',text,flags=re.MULTILINE)
    text=re.sub(r'\n+',' ',text)
    text=re.sub(r'\s+',' ',text)
    text=text.strip()
    if len(text)>max_length:
        text=text[:max_length-3].strip()+"..."
    return text

app=create_app()

init_db()

@app.before_request
def apply_ip_rate_limits():
    ip=request.remote_addr
    path=request.path
    if path.startswith("/static/") or path.startswith("/uploads/"):
        return None
    user=get_current_user(request)
    if path in ["/signup","/signin"] and request.method=="POST":
        allowed,retry=check_ip_rate_limit(ip,"auth",5,60)
        if not allowed:
            return render_template("error.html",user=user,error="Too many requests. Please try again later."),429
    if request.method in ["POST","PUT","DELETE"]:
        allowed,retry=check_ip_rate_limit(ip,"write",5,60)
        if not allowed:
            return render_template("error.html",user=user,error="Too many requests. Please try again later."),429
    allowed,retry=check_ip_rate_limit(ip,"general",60,60)
    if not allowed:
        return render_template("error.html",user=user,error="Too many requests. Please try again later."),429
    return None

@app.route("/uploads/<path:file>")
def serve_upload(file):
    return send_from_directory("data/uploads",file)

@app.template_filter("timestampformat")
def timestampformat_filter(value,format="%B %d, %Y at %I:%M %p"):
    if isinstance(value,int):
        try:
            dt=datetime.fromtimestamp(value)
            return dt.strftime(format)
        except:
            return str(value)
    return value

@app.template_filter("avatar")
def avatar_filter(user):
    return get_avatar_url(user)

@app.template_filter("clean_markdown")
def clean_markdown_filter(text):
    return clean_markdown_for_og(text)

@app.route("/")
def home():
    user=get_current_user(request)
    page=request.args.get("page",1,type=int)
    if page<1:
        page=1
    blogs,total_count,total_pages,current_page=get_recent_blogs(page=page)
    return render_template("home.html",user=user,blogs=blogs,current_page=current_page,total_pages=total_pages,total_count=total_count)

@app.route("/signup",methods=["GET"])
def signup_page():
    user=get_current_user(request)
    return render_template("signup.html",user=user)

@app.route("/signup",methods=["POST"])
def signup():
    username=request.form.get("username","").strip()
    display_name=request.form.get("display_name","").strip()
    password=request.form.get("password","")
    terms_accepted=request.form.get("terms_accepted")
    if not terms_accepted:
        user=get_current_user(request)
        return render_template("signup.html",user=user,error="You must accept the Terms of Service and Privacy Policy to create an account")
    user_id,error=register_user(username,display_name,password)
    if error:
        user=get_current_user(request)
        return render_template("signup.html",user=user,error=error)
    token=create_session(user_id,request.headers.get("User-Agent","Unknown"))
    response=make_response(redirect(url_for("home")))
    response.set_cookie("session_token",token,max_age=2592000,httponly=True,secure=False,samesite="Lax")
    return response

@app.route("/signin",methods=["GET"])
def signin_page():
    user=get_current_user(request)
    return render_template("signin.html",user=user)

@app.route("/signin",methods=["POST"])
def signin():
    username=request.form.get("username","").strip()
    password=request.form.get("password","")
    token,error=login_user(username,password,request.headers.get("User-Agent","Unknown"))
    if error:
        user=get_current_user(request)
        return render_template("signin.html",user=user,error=error)
    response=make_response(redirect(url_for("home")))
    response.set_cookie("session_token",token,max_age=2592000,httponly=True,secure=False,samesite="Lax")
    return response

@app.route("/logout")
def logout():
    token=request.cookies.get("session_token")
    if token:
        delete_session(token)
    response=make_response(redirect(url_for("home")))
    response.set_cookie("session_token","",max_age=0)
    return response

@app.route("/search")
def search():
    user=get_current_user(request)
    query=request.args.get("q","").strip()
    page=request.args.get("page",1,type=int)
    if page<1:
        page=1
    blogs,total_count,total_pages,current_page=search_blogs(query,page=page) if query else ([],0,0,1)
    return render_template("search.html",user=user,query=query,blogs=blogs,current_page=current_page,total_pages=total_pages,total_count=total_count)

@app.route("/profile/<username>")
def profile(username):
    user=get_current_user(request)
    profile_user=get_user_by_username(username)
    if not profile_user:
        return render_template("error.html",user=user,error="User not found"),404
    is_own_profile=user and user["id"]==profile_user["id"]
    page=request.args.get("page",1,type=int)
    if page<1:
        page=1
    blogs,total_count,total_pages,current_page=get_user_blogs(profile_user["id"],include_drafts=is_own_profile,page=page)
    return render_template("profile.html",user=user,profile_user=profile_user,blogs=blogs,is_own_profile=is_own_profile,current_page=current_page,total_pages=total_pages,total_count=total_count)

@app.route("/blog/new",methods=["GET"])
def new_blog_page():
    user=get_current_user(request)
    if not user:
        return redirect(url_for("signin_page"))
    return render_template("blog_new.html",user=user)

@app.route("/blog/new",methods=["POST"])
def new_blog():
    user=get_current_user(request)
    if not user:
        return redirect(url_for("signin_page"))
    allowed,retry=check_user_rate_limit(user["id"],"blog_create",10,3600)
    if not allowed:
        return render_template("blog_new.html",user=user,error="Too many requests. Please try again later.")
    title=request.form.get("title","").strip()
    content=request.form.get("content","").strip()
    is_draft=1 if "is_draft" in request.form else 0
    blog_id,error=create_blog(user["id"],title,content,is_draft)
    if error:
        return render_template("blog_new.html",user=user,error=error)
    return redirect(url_for("view_blog",id=blog_id))

@app.route("/blog/<id>")
def view_blog(id):
    user=get_current_user(request)
    blog=get_blog(id)
    if not blog:
        return render_template("error.html",user=user,error="Blog not found"),404
    if blog["is_draft"] and (not user or user["id"]!=blog["user_id"]):
        return render_template("error.html",user=user,error="Blog not found"),404
    comments=get_blog_comments(id)
    comment_tree=build_comment_tree(comments)
    return render_template("blog_view.html",user=user,blog=blog,comments=comment_tree)

@app.route("/blog/<id>/edit",methods=["GET"])
def edit_blog_page(id):
    user=get_current_user(request)
    if not user:
        return redirect(url_for("signin_page"))
    blog=get_blog(id)
    if not blog:
        return render_template("error.html",user=user,error="Blog not found"),404
    if blog["user_id"]!=user["id"]:
        return render_template("error.html",user=user,error="Unauthorized"),403
    return render_template("blog_edit.html",user=user,blog=blog)

@app.route("/blog/<id>/edit",methods=["POST"])
def edit_blog(id):
    user=get_current_user(request)
    if not user:
        return redirect(url_for("signin_page"))
    title=request.form.get("title","").strip()
    content=request.form.get("content","").strip()
    is_draft=1 if "is_draft" in request.form else 0
    success,error=update_blog(id,user["id"],title,content,is_draft)
    if not success:
        blog=get_blog(id)
        return render_template("blog_edit.html",user=user,blog=blog,error=error)
    return redirect(url_for("view_blog",id=id))

@app.route("/blog/<id>/delete",methods=["POST"])
def delete_blog_route(id):
    user=get_current_user(request)
    if not user:
        return jsonify({"success":False,"error":"Unauthorized"}),401
    success,error=delete_blog(id,user["id"])
    if not success:
        return jsonify({"success":False,"error":error}),400
    return jsonify({"success":True})

@app.route("/blog/<id>/comment",methods=["POST"])
def add_comment(id):
    user=get_current_user(request)
    if not user:
        return redirect(url_for("signin_page"))
    allowed,retry=check_user_rate_limit(user["id"],"comment_create",30,3600)
    if not allowed:
        blog=get_blog(id)
        if not blog:
            return render_template("error.html",user=user,error="Blog not found"),404
        comments=get_blog_comments(id)
        comment_tree=build_comment_tree(comments)
        return render_template("blog_view.html",user=user,blog=blog,comments=comment_tree,error="Too many requests. Please try again later.")
    content=request.form.get("content","").strip()
    parent_id=request.form.get("parent_id")
    parent_id=parent_id if parent_id else None
    comment_id,mention_username=create_comment(id,user["id"],content,parent_id)
    if not comment_id:
        blog=get_blog(id)
        if not blog:
            return render_template("error.html",user=user,error="Blog not found"),404
        comments=get_blog_comments(id)
        comment_tree=build_comment_tree(comments)
        return render_template("blog_view.html",user=user,blog=blog,comments=comment_tree,error=mention_username)
    if mention_username:
        content=f"@{mention_username} {content}"
        updated_at=int(time.time())
        execute_db("UPDATE comments SET content=?,updated_at=? WHERE id=?",(content,updated_at,comment_id))
    return redirect(url_for("view_blog",id=id))

@app.route("/comment/<id>/delete",methods=["POST"])
def delete_comment_route(id):
    user=get_current_user(request)
    if not user:
        return jsonify({"success":False,"error":"Unauthorized"}),401
    success,error=delete_comment(id,user["id"])
    if not success:
        return jsonify({"success":False,"error":error}),400
    return jsonify({"success":True})

@app.route("/settings")
def settings():
    user=get_current_user(request)
    if not user:
        return redirect(url_for("signin_page"))
    sessions=get_user_sessions(user["id"])
    current_token=request.cookies.get("session_token")
    return render_template("settings.html",user=user,sessions=sessions,current_token=current_token)

@app.route("/settings/display-name",methods=["POST"])
def update_display_name():
    user=get_current_user(request)
    if not user:
        return redirect(url_for("signin_page"))
    allowed,retry=check_user_rate_limit(user["id"],"settings_update",15,60)
    if not allowed:
        sessions=get_user_sessions(user["id"])
        current_token=request.cookies.get("session_token")
        return render_template("settings.html",user=user,sessions=sessions,current_token=current_token,error="Too many requests. Please try again later.")
    display_name=request.form.get("display_name","").strip()
    if not display_name or len(display_name)<1 or len(display_name)>50:
        sessions=get_user_sessions(user["id"])
        current_token=request.cookies.get("session_token")
        return render_template("settings.html",user=user,sessions=sessions,current_token=current_token,error="Display name must be 1-50 characters")
    execute_db("UPDATE users SET display_name=? WHERE id=?",(display_name,user["id"]))
    return redirect(url_for("settings"))

@app.route("/settings/profile-picture",methods=["POST"])
def upload_profile_picture():
    user=get_current_user(request)
    if not user:
        return redirect(url_for("signin_page"))
    allowed,retry=check_user_rate_limit(user["id"],"settings_update",15,60)
    if not allowed:
        sessions=get_user_sessions(user["id"])
        current_token=request.cookies.get("session_token")
        return render_template("settings.html",user=user,sessions=sessions,current_token=current_token,error="Too many requests. Please try again later.")
    if "file" not in request.files:
        return redirect(url_for("settings"))
    file=request.files["file"]
    if file.filename=="":
        return redirect(url_for("settings"))
    old_picture_path=None
    if user.get("profile_picture"):
        old_picture_path=os.path.join("data/uploads",user["profile_picture"])
    filename,error=save_profile_picture(file,user["id"],old_picture_path)
    if error:
        sessions=get_user_sessions(user["id"])
        current_token=request.cookies.get("session_token")
        return render_template("settings.html",user=user,sessions=sessions,current_token=current_token,error=error)
    update_profile_picture(user["id"],filename)
    return redirect(url_for("settings"))

@app.route("/settings/sessions/delete",methods=["POST"])
def delete_session_route():
    user=get_current_user(request)
    if not user:
        return jsonify({"success":False,"error":"Unauthorized"}),401
    data=request.get_json()
    token=data.get("token")
    if not token:
        return jsonify({"success":False,"error":"Token required"}),400
    success=delete_session_by_id(token,user["id"])
    if not success:
        return jsonify({"success":False,"error":"Session not found"}),404
    return jsonify({"success":True})

@app.route("/api/upload-image",methods=["POST"])
def upload_blog_image():
    user=get_current_user(request)
    if not user:
        return jsonify({"success":False,"error":"Unauthorized"}),401
    allowed,retry=check_user_rate_limit(user["id"],"image_upload",20,3600)
    if not allowed:
        return jsonify({"success":False,"error":"Too many requests. Try again later."}),429
    if "file" not in request.files:
        return jsonify({"success":False,"error":"No file provided"}),400
    file=request.files["file"]
    if file.filename=="":
        return jsonify({"success":False,"error":"No file selected"}),400
    filename,error=save_blog_image(file)
    if error:
        return jsonify({"success":False,"error":error}),400
    return jsonify({"success":True,"url":f"/uploads/blog_images/{filename}"})

@app.route("/api/delete-account",methods=["POST"])
def delete_account_route():
    user=get_current_user(request)
    if not user:
        return jsonify({"success":False,"error":"Unauthorized"}),401
    username=request.form.get("username","").strip()
    confirmation=request.form.get("confirmation","").strip()
    if username!=user["username"]:
        return jsonify({"success":False,"error":"Username does not match"}),400
    if confirmation!="DELETE":
        return jsonify({"success":False,"error":"Confirmation text does not match"}),400
    try:
        delete_user(user["id"])
        return jsonify({"success":True,"message":"Account deleted successfully"})
    except Exception as e:
        return jsonify({"success":False,"error":"Failed to delete account"}),500

@app.route("/terms")
def terms_page():
    user=get_current_user(request)
    return render_template("terms.html",user=user)

@app.route("/privacy")
def privacy_page():
    user=get_current_user(request)
    return render_template("privacy.html",user=user)

@app.route("/rules")
def rules_page():
    user=get_current_user(request)
    return render_template("rules.html",user=user)

@app.route("/robots.txt")
def robots_txt():
    user=get_current_user(request)
    robots_content="""User-agent: *
Allow: /
Allow: /blog/
Allow: /profile/
Allow: /search

Disallow: /settings
Disallow: /signin
Disallow: /signup
Disallow: /logout
Disallow: /blog/new
Disallow: /blog/*/edit
Disallow: /blog/*/delete
Disallow: /comment/*/delete
Disallow: /settings/
Disallow: /api/
Disallow: /uploads/temp/
Disallow: /admin
Disallow: /admin/

Sitemap: """+request.base_url.rstrip('/')+"/sitemap.xml"
    response=make_response(robots_content)
    response.headers["Content-Type"]="text/plain"
    return response

@app.route("/sitemap.xml")
def sitemap_xml():
    user=get_current_user(request)
    base_url=request.base_url.rstrip('/')
    sitemap=[ '<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap.append(f'<url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>')
    sitemap.append(f'<url><loc>{base_url}/terms</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>')
    sitemap.append(f'<url><loc>{base_url}/privacy</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>')
    sitemap.append(f'<url><loc>{base_url}/rules</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>')
    blogs=execute_db("SELECT id,updated_at FROM blogs WHERE is_draft=0 ORDER BY updated_at DESC LIMIT 50000").fetchall()
    for blog in blogs:
        sitemap.append(f'<url><loc>{base_url}/blog/{blog["id"]}</loc><lastmod>{datetime.fromtimestamp(blog["updated_at"]).strftime("%Y-%m-%d")}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>')
    sitemap.append('</urlset>')
    sitemap_content='\n'.join(sitemap)
    response=make_response(sitemap_content)
    response.headers["Content-Type"]="application/xml"
    return response

@app.route("/health")
def health_check():
    return "OK",200

@app.route("/admin")
@require_admin
def admin_dashboard():
    user=get_current_user(request)
    stats=get_user_stats()
    db_version=get_db_version()
    return render_template("admin/dashboard.html",user=user,stats=stats,db_version=db_version)

@app.route("/admin/users")
@require_admin
def admin_users():
    user=get_current_user(request)
    page=request.args.get("page",1,type=int)
    search=request.args.get("search","").strip()
    if page<1:
        page=1
    users=get_all_users(limit=50,offset=(page-1)*50,search=search)
    return render_template("admin/users.html",user=user,users=users,current_page=page,search=search)

@app.route("/admin/blogs")
@require_admin
def admin_blogs():
    user=get_current_user(request)
    page=request.args.get("page",1,type=int)
    if page<1:
        page=1
    offset=(page-1)*50
    blogs=execute_db("""
        SELECT b.*, u.username, u.display_name
        FROM blogs b
        JOIN users u ON b.user_id = u.id
        ORDER BY b.created_at DESC
        LIMIT 50 OFFSET ?
    """,(offset,))
    total_blogs=execute_db("SELECT COUNT(*) as count FROM blogs",one=True).fetchone()["count"]
    total_pages=(total_blogs+49)//50
    return render_template("admin/blogs.html",user=user,blogs=blogs,current_page=page,total_pages=total_pages,total_blogs=total_blogs)

@app.route("/admin/comments")
@require_admin
def admin_comments():
    user=get_current_user(request)
    page=request.args.get("page",1,type=int)
    if page<1:
        page=1
    offset=(page-1)*50
    comments=execute_db("""
        SELECT c.*, u.username, u.display_name, b.title as blog_title
        FROM comments c
        JOIN users u ON c.user_id = u.id
        JOIN blogs b ON c.blog_id = b.id
        ORDER BY c.created_at DESC
        LIMIT 50 OFFSET ?
    """,(offset,))
    total_comments=execute_db("SELECT COUNT(*) as count FROM comments",one=True).fetchone()["count"]
    total_pages=(total_comments+49)//50
    return render_template("admin/comments.html",user=user,comments=comments,current_page=page,total_pages=total_pages,total_comments=total_comments)

@app.route("/admin/promote/<user_id>",methods=["POST"])
@require_admin
def admin_promote_user(user_id):
    user=get_current_user(request)
    success,message=promote_user_to_admin(user["id"],user_id)
    return jsonify({"success":success,"message":message})

@app.route("/admin/demote/<user_id>",methods=["POST"])
@require_admin
def admin_demote_user(user_id):
    user=get_current_user(request)
    success,message=demote_admin_to_user(user["id"],user_id)
    return jsonify({"success":success,"message":message})

@app.route("/admin/delete-user/<user_id>",methods=["POST"])
@require_admin
def admin_delete_user(user_id):
    user=get_current_user(request)
    target_user=execute_db("SELECT role FROM users WHERE id=?",(user_id,),one=True).fetchone()
    if not target_user:
        return jsonify({"success":False,"error":"User not found"}),404
    if target_user["role"]=="admin":
        admin_count=execute_db("SELECT COUNT(*) as count FROM users WHERE role='admin'",one=True).fetchone()["count"]
        if admin_count<=1:
            return jsonify({"success":False,"error":"Cannot delete the last admin"}),400
    try:
        execute_db("DELETE FROM users WHERE id=?",(user_id,))
        return jsonify({"success":True,"message":"User deleted successfully"})
    except Exception as e:
        return jsonify({"success":False,"error":"Failed to delete user"}),500

@app.route("/admin/delete-blog/<blog_id>",methods=["POST"])
@require_admin
def admin_delete_blog(blog_id):
    user=get_current_user(request)
    blog=execute_db("SELECT id FROM blogs WHERE id=?",(blog_id,),one=True).fetchone()
    if not blog:
        return jsonify({"success":False,"error":"Blog not found"}),404
    try:
        execute_db("DELETE FROM blogs WHERE id=?",(blog_id,))
        return jsonify({"success":True,"message":"Blog deleted successfully"})
    except Exception as e:
        return jsonify({"success":False,"error":"Failed to delete blog"}),500

@app.route("/admin/delete-comment/<comment_id>",methods=["POST"])
@require_admin
def admin_delete_comment(comment_id):
    user=get_current_user(request)
    comment=execute_db("SELECT id FROM comments WHERE id=?",(comment_id,),one=True).fetchone()
    if not comment:
        return jsonify({"success":False,"error":"Comment not found"}),404
    try:
        execute_db("DELETE FROM comments WHERE id=?",(comment_id,))
        return jsonify({"success":True,"message":"Comment deleted successfully"})
    except Exception as e:
        return jsonify({"success":False,"error":"Failed to delete comment"}),500

@app.errorhandler(404)
def not_found_error(error):
    user=get_current_user(request)
    return render_template("error.html",user=user,error="Page not found"),404

@app.errorhandler(405)
def method_not_allowed_error(error):
    user=get_current_user(request)
    return render_template("error.html",user=user,error="Method not allowed"),405

@app.errorhandler(413)
def request_entity_too_large_error(error):
    user=get_current_user(request)
    return render_template("error.html",user=user,error="File too large"),413

@app.errorhandler(500)
def internal_server_error(error):
    user=get_current_user(request)
    return render_template("error.html",user=user,error="Internal server error"),500

if __name__=="__main__":
    serve(app,host="0.0.0.0",port=4782,threads=32)
