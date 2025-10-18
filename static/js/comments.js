function showReplyForm(commentId){
document.querySelectorAll(".reply-form").forEach(f=>f.remove());
const form=document.createElement("form");
form.className="reply-form";
form.innerHTML=`<textarea name="content" placeholder="Write a reply..." required></textarea><input type="hidden" name="parent_id" value="${commentId}"><div style="margin-top:10px;"><button type="submit" class="btn btn-small">Reply</button> <button type="button" class="btn btn-secondary btn-small" onclick="this.closest('.reply-form').remove()">Cancel</button></div>`;
document.querySelector(`[data-comment-id="${commentId}"]`).appendChild(form);
}
function deleteComment(commentId){
commentId=String(commentId).trim();
if(!commentId){
alert("Invalid comment ID");
return;
}
if(confirm("Are you sure you want to delete this comment?")){
fetch(`/comment/${commentId}/delete`,{method:"POST",headers:{"Content-Type":"application/json"}}).then(r=>r.json()).then(data=>{
if(data.success){
location.reload();
}else{
alert(data.error||"Failed to delete comment");
}
}).catch(err=>{
console.error("Delete error:",err);
alert("Failed to delete comment");
});
}
}
function deleteBlog(blogId){
if(confirm("Are you sure you want to delete this blog? This action cannot be undone.")){
fetch(`/blog/${blogId}/delete`,{method:"POST"}).then(r=>r.json()).then(data=>{
if(data.success){
window.location.href="/";
}else{
alert(data.error||"Failed to delete blog");
}
}).catch(()=>alert("Failed to delete blog"));
}
}
function deleteSession(token){
if(confirm("Are you sure you want to end this session?")){
fetch("/settings/sessions/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token})}).then(r=>r.json()).then(data=>{
if(data.success){
location.reload();
}else{
alert(data.error||"Failed to delete session");
}
}).catch(()=>alert("Failed to delete session"));
}
}
