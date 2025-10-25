function toggleTheme(){
const currentTheme=document.documentElement.getAttribute("data-theme");
const newTheme=currentTheme==="dark"?"light":"dark";
document.documentElement.setAttribute("data-theme",newTheme);
localStorage.setItem("theme",newTheme);
const toggleBtn=document.getElementById("theme-toggle");
if(toggleBtn){
toggleBtn.textContent=newTheme==="dark"?"☀️":"🌙";
}
}

function toggleMobileMenu(){
const mobileMenu=document.getElementById("mobileMenu");
if(mobileMenu){
mobileMenu.classList.toggle("active");
document.body.style.overflow=mobileMenu.classList.contains("active")?"hidden":"auto";
}
}

document.addEventListener("DOMContentLoaded",()=>{
const theme=localStorage.getItem("theme")||"light";
document.documentElement.setAttribute("data-theme",theme);
const toggleBtn=document.getElementById("theme-toggle");
if(toggleBtn){
toggleBtn.textContent=theme==="dark"?"☀️":"🌙";
toggleBtn.addEventListener("click",toggleTheme);
}
});
