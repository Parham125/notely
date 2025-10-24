function showMessage(message,type='info'){
const container=document.getElementById('message-container');
if(!container)return;
const messageDiv=document.createElement('div');
messageDiv.className=`message ${type}`;
messageDiv.textContent=message;
container.appendChild(messageDiv);
setTimeout(()=>{
messageDiv.style.opacity='0';
setTimeout(()=>container.removeChild(messageDiv),300);
},5000);
}

async function adminRequest(url,method='POST',body=null){
try{
const options={
method,
headers:{
'Content-Type':'application/json',
'X-Requested-With':'XMLHttpRequest'
}
};
if(body){
options.body=JSON.stringify(body);
}
const response=await fetch(url,options);
const result=await response.json();
if(result.success){
showMessage(result.message||'Operation completed successfully','success');
setTimeout(()=>window.location.reload(),1500);
}else{
showMessage(result.error||'Operation failed','error');
}
return result;
}catch(error){
console.error('Admin request error:',error);
showMessage('Network error occurred','error');
return{success:false,error:'Network error'};
}
}

async function promoteUser(userId,username){
if(!confirm(`Are you sure you want to promote ${username} to admin?`))return;
await adminRequest(`/admin/promote/${userId}`);
}

async function demoteUser(userId,username){
if(!confirm(`Are you sure you want to demote ${username} from admin to user?\n\n⚠️ Warning: This cannot be undone if this is the last admin.`))return;
await adminRequest(`/admin/demote/${userId}`);
}

async function deleteUser(userId,username){
if(!confirm(`Are you sure you want to delete user ${username}?\n\n⚠️ This will permanently delete all their blogs and comments. This action cannot be undone.`))return;
await adminRequest(`/admin/delete-user/${userId}`);
}

async function deleteBlog(blogId,title){
if(!confirm(`Are you sure you want to delete blog "${title}"?\n\n⚠️ This will permanently delete the blog and all its comments. This action cannot be undone.`))return;
await adminRequest(`/admin/delete-blog/${blogId}`);
}

async function deleteComment(commentId){
if(!confirm(`Are you sure you want to delete this comment?\n\n⚠️ This action cannot be undone.`))return;
await adminRequest(`/admin/delete-comment/${commentId}`);
}

document.addEventListener('DOMContentLoaded',function(){
const messageContainer=document.getElementById('message-container');
if(messageContainer){
messageContainer.style.position='fixed';
messageContainer.style.top='20px';
messageContainer.style.right='20px';
messageContainer.style.zIndex='1000';
messageContainer.style.maxWidth='400px';
}
});