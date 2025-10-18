document.addEventListener("DOMContentLoaded",()=>{
const theme=localStorage.getItem("theme")||"light";
document.documentElement.setAttribute("data-theme",theme);
const toggleBtn=document.getElementById("theme-toggle");
if(toggleBtn){
toggleBtn.textContent=theme==="dark"?"☀️":"🌙";
toggleBtn.addEventListener("click",()=>{
const currentTheme=document.documentElement.getAttribute("data-theme");
const newTheme=currentTheme==="dark"?"light":"dark";
document.documentElement.setAttribute("data-theme",newTheme);
localStorage.setItem("theme",newTheme);
toggleBtn.textContent=newTheme==="dark"?"☀️":"🌙";
});
}
});
