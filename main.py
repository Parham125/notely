from flask import request,render_template,redirect,url_for,make_response,jsonify,send_from_directory
from datetime import datetime
from waitress import serve
import os
from config import create_app
from database import init_db,execute_db
from auth import get_current_user,register_user,login_user,delete_session,delete_session_by_id,get_user_sessions,create_session,update_profile_picture
from blog_ops import get_recent_blogs,create_blog,get_blog,update_blog,delete_blog,get_user_blogs,search_blogs,get_user_by_username
from comment_ops import create_comment,delete_comment,get_blog_comments,build_comment_tree
from file_handler import save_profile_picture,save_blog_image
from avatar_generator import get_avatar_url
from rate_limiter import check_ip_rate_limit,check_user_rate_limit

app=create_app()

if not os.path.exists("data/notely.db"):
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
        allowed,retry=check_ip_rate_limit(ip,"write",20,60)
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

@app.route("/")
def home():
    user=get_current_user(request)
    blogs=get_recent_blogs()
    return render_template("home.html",user=user,blogs=blogs)

@app.route("/signup",methods=["GET"])
def signup_page():
    user=get_current_user(request)
    return render_template("signup.html",user=user)

@app.route("/signup",methods=["POST"])
def signup():
    username=request.form.get("username","").strip()
    display_name=request.form.get("display_name","").strip()
    password=request.form.get("password","")
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
    blogs=search_blogs(query) if query else []
    return render_template("search.html",user=user,query=query,blogs=blogs)

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
    comment_id,error=create_comment(id,user["id"],content,parent_id)
    if error:
        blog=get_blog(id)
        if not blog:
            return render_template("error.html",user=user,error="Blog not found"),404
        comments=get_blog_comments(id)
        comment_tree=build_comment_tree(comments)
        return render_template("blog_view.html",user=user,blog=blog,comments=comment_tree,error=error)
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

@app.route("/health")
def health_check():
    return "OK",200

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
