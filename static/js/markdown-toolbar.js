function initMarkdownToolbar(textareaId){
const textarea=document.getElementById(textareaId);
if(!textarea)return;
const wrapper=document.createElement("div");
wrapper.style.cssText="display:grid;grid-template-columns:1fr 1fr;gap:20px;";
const leftPanel=document.createElement("div");
const rightPanel=document.createElement("div");
const toolbar=document.createElement("div");
toolbar.className="markdown-toolbar";
const buttons=[
{label:"H1",action:()=>insertMarkdown(textarea,"# ","",true)},
{label:"H2",action:()=>insertMarkdown(textarea,"## ","",true)},
{label:"H3",action:()=>insertMarkdown(textarea,"### ","",true)},
{label:"Bold",action:()=>insertMarkdown(textarea,"**","**")},
{label:"Italic",action:()=>insertMarkdown(textarea,"*","*")},
{label:"Underline",action:()=>insertMarkdown(textarea,"__","__")},
{label:"Strike",action:()=>insertMarkdown(textarea,"~~","~~")},
{label:"Code",action:()=>insertMarkdown(textarea,"`","`")},
{label:"Link",action:()=>insertLink(textarea)},
{label:"Quote",action:()=>insertMarkdown(textarea,"> ","",true)},
{label:"Note",action:()=>insertMarkdown(textarea,"> [!NOTE] ","",true)},
{label:"Important",action:()=>insertMarkdown(textarea,"> [!IMPORTANT] ","",true)},
{label:"Warning",action:()=>insertMarkdown(textarea,"> [!WARNING] ","",true)},
{label:"Error",action:()=>insertMarkdown(textarea,"> [!ERROR] ","",true)},
{label:"List",action:()=>insertMarkdown(textarea,"- ","",true)},
{label:"Task",action:()=>insertMarkdown(textarea,"- [ ] ","",true)},
{label:"Highlight",action:()=>insertMarkdown(textarea,"==","==")},
{label:"Sub",action:()=>insertMarkdown(textarea,"~","~")},
{label:"Super",action:()=>insertMarkdown(textarea,"^","^")},
{label:"Code Block",action:()=>insertCodeBlock(textarea)},
{label:"Image",action:()=>openImageModal(textarea)}
];
buttons.forEach(btn=>{
const button=document.createElement("button");
button.textContent=btn.label;
button.type="button";
button.onclick=(e)=>{e.preventDefault();btn.action();};
toolbar.appendChild(button);
});
textarea.parentNode.insertBefore(wrapper,textarea);
leftPanel.appendChild(toolbar);
leftPanel.appendChild(textarea);
const previewContainer=document.createElement("div");
previewContainer.innerHTML='<div class="markdown-toolbar" style="justify-content:space-between;"><span style="font-weight:600;">Live Preview</span></div><div id="markdown-preview" class="blog-content" style="border:1px solid var(--border);border-radius:6px;padding:20px;min-height:400px;background:var(--bg);"></div>';
rightPanel.appendChild(previewContainer);
wrapper.appendChild(leftPanel);
wrapper.appendChild(rightPanel);
textarea.classList.add("markdown-toolbar-textarea");
textarea.addEventListener("input",()=>updatePreview(textarea));
updatePreview(textarea);
}
function insertMarkdown(textarea,prefix,suffix,newLine=false){
const start=textarea.selectionStart;
const end=textarea.selectionEnd;
const text=textarea.value;
const selectedText=text.substring(start,end);
let newText,cursorPos;
if(selectedText){
newText=text.substring(0,start)+prefix+selectedText+suffix+text.substring(end);
cursorPos=start+prefix.length+selectedText.length+suffix.length;
}else{
if(newLine){
const lineStart=text.lastIndexOf("\n",start-1)+1;
newText=text.substring(0,lineStart)+prefix+text.substring(lineStart);
cursorPos=lineStart+prefix.length;
}else{
newText=text.substring(0,start)+prefix+suffix+text.substring(end);
cursorPos=start+prefix.length;
}
}
textarea.value=newText;
textarea.focus();
textarea.setSelectionRange(cursorPos,cursorPos);
updatePreview(textarea);
}
function insertLink(textarea){
const url=prompt("Enter URL:");
if(!url)return;
const text=prompt("Enter link text:")||url;
const start=textarea.selectionStart;
const markdown=`[${text}](${url})`;
textarea.value=textarea.value.substring(0,start)+markdown+textarea.value.substring(textarea.selectionEnd);
textarea.focus();
const newPos=start+markdown.length;
textarea.setSelectionRange(newPos,newPos);
updatePreview(textarea);
}
function insertCodeBlock(textarea){
const lang=prompt("Enter language (python, javascript, etc.):")||"";
const start=textarea.selectionStart;
const markdown=`\`\`\`${lang}\ncode here\n\`\`\`\n`;
textarea.value=textarea.value.substring(0,start)+markdown+textarea.value.substring(textarea.selectionEnd);
textarea.focus();
const newPos=start+lang.length+4;
textarea.setSelectionRange(newPos,newPos+9);
updatePreview(textarea);
}
function openImageModal(textarea){
const overlay=document.createElement("div");
overlay.className="modal-overlay active";
const modal=document.createElement("div");
modal.className="image-upload-modal active";
modal.innerHTML=`<h3>Insert Image</h3><div class="form-group"><label>Upload Image</label><input type="file" id="image-upload-input" accept="image/*"></div><div class="form-group"><label>Or enter image URL</label><input type="text" id="image-url-input" placeholder="https://example.com/image.jpg"></div><div class="form-group"><label>Alt Text</label><input type="text" id="image-alt-input" placeholder="Image description"></div><div style="display:flex;gap:10px;"><button class="btn" id="insert-image-btn">Insert</button><button class="btn btn-secondary" id="cancel-image-btn">Cancel</button></div>`;
document.body.appendChild(overlay);
document.body.appendChild(modal);
const closeModal=()=>{overlay.remove();modal.remove();};
document.getElementById("cancel-image-btn").onclick=closeModal;
overlay.onclick=closeModal;
document.getElementById("insert-image-btn").onclick=async()=>{
const fileInput=document.getElementById("image-upload-input");
const urlInput=document.getElementById("image-url-input");
const altInput=document.getElementById("image-alt-input");
const alt=altInput.value||"image";
if(fileInput.files.length>0){
const formData=new FormData();
formData.append("file",fileInput.files[0]);
try{
const response=await fetch("/api/upload-image",{method:"POST",body:formData});
const data=await response.json();
if(data.success){
insertImageMarkdown(textarea,data.url,alt);
}else{
alert(data.error||"Upload failed");
}
}catch(err){
alert("Upload failed: "+err.message);
}
}else if(urlInput.value){
insertImageMarkdown(textarea,urlInput.value,alt);
}else{
alert("Please select an image or enter a URL");
return;
}
closeModal();
};
}
function insertImageMarkdown(textarea,url,alt){
const start=textarea.selectionStart;
const markdown=`![${alt}](${url})`;
textarea.value=textarea.value.substring(0,start)+markdown+textarea.value.substring(textarea.selectionEnd);
textarea.focus();
const newPos=start+markdown.length;
textarea.setSelectionRange(newPos,newPos);
updatePreview(textarea);
}
function updatePreview(textarea){
const preview=document.getElementById("markdown-preview");
if(!preview)return;
const html=renderMarkdownClient(textarea.value);
preview.innerHTML=html;
if(typeof hljs!=="undefined"){
preview.querySelectorAll("pre code").forEach(block=>hljs.highlightElement(block));
}
}
