function renderMarkdownClient(text){
if(!text)return"";
const codeBlocks=[];
text=text.replace(/```(\w+)?\n([\s\S]*?)```/g,(m,lang,code)=>{
const escapedCode=code.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
const langAttr=lang?` class="language-${lang.replace(/[<>"]/g,"")}"`:"";
const html=`<pre><code${langAttr}>${escapedCode}</code></pre>`;
codeBlocks.push(html);
return`___CODE_BLOCK_${codeBlocks.length-1}___`;
});
const lines=text.split(/\r?\n/);
let result=[];
let inQuote=false;
let quoteContent=[];
let calloutType=null;
let calloutTitle=null;
let inTaskList=false;
let inUnorderedList=false;
let inOrderedList=false;
for(let i=0;i<lines.length;i++){
const line=lines[i];
if(line.match(/^___CODE_BLOCK_\d+___$/)){
if(inTaskList){result.push("</ul>");inTaskList=false;}
if(inUnorderedList){result.push("</ul>");inUnorderedList=false;}
if(inOrderedList){result.push("</ol>");inOrderedList=false;}
if(inQuote){
const paragraphs=quoteContent.filter(l=>l.trim()).map(l=>`<p>${renderInline(l)}</p>`);
const content=paragraphs.join("");
result.push(`<blockquote${calloutType?` class="callout callout-${calloutType.toLowerCase()}"`:""}>${calloutTitle?`<div class="callout-title">${calloutTitle}</div>`:""}${content}</blockquote>`);
quoteContent=[];
inQuote=false;
calloutType=null;
calloutTitle=null;
}
result.push(line);
continue;
}
const calloutMatch=line.match(/^>\s*\[!(IMPORTANT|WARNING|NOTE|CAUTION|TIP)\]\s*(.*)$/);
if(calloutMatch){
if(inQuote&&calloutType!==calloutMatch[1]){
const paragraphs=quoteContent.filter(l=>l.trim()).map(l=>`<p>${renderInline(l)}</p>`);
const content=paragraphs.join("");
result.push(`<blockquote class="callout callout-${calloutType.toLowerCase()}">${calloutTitle?`<div class="callout-title">${calloutTitle}</div>`:""}${content}</blockquote>`);
quoteContent=[];
}
calloutType=calloutMatch[1];
calloutTitle=calloutMatch[2].trim()||calloutMatch[1];
inQuote=true;
continue;
}
const quoteMatch=line.match(/^>\s*(.*)$/);
if(quoteMatch){
if(!inQuote)inQuote=true;
quoteContent.push(quoteMatch[1]);
continue;
}
if(inQuote){
const paragraphs=quoteContent.filter(l=>l.trim()).map(l=>`<p>${renderInline(l)}</p>`);
const content=paragraphs.join("");
result.push(`<blockquote${calloutType?` class="callout callout-${calloutType.toLowerCase()}"`:""}>${calloutTitle?`<div class="callout-title">${calloutTitle}</div>`:""}${content}</blockquote>`);
quoteContent=[];
inQuote=false;
calloutType=null;
calloutTitle=null;
}
const heading=line.match(/^(#{1,6})\s+(.+)$/);
if(heading){
if(inTaskList){result.push("</ul>");inTaskList=false;}
if(inUnorderedList){result.push("</ul>");inUnorderedList=false;}
if(inOrderedList){result.push("</ol>");inOrderedList=false;}
result.push(`<h${heading[1].length}>${renderInline(heading[2])}</h${heading[1].length}>`);
continue;
}
const task=line.match(/^[-*+]\s+\[([ xX])\]\s+(.+)$/);
if(task){
if(inUnorderedList){result.push("</ul>");inUnorderedList=false;}
if(inOrderedList){result.push("</ol>");inOrderedList=false;}
if(!inTaskList){result.push("<ul class=\"task-list\">");inTaskList=true;}
const checked=task[1].toLowerCase()==="x"?"checked":"";
result.push(`<li><input type="checkbox" ${checked} disabled>${renderInline(task[2])}</li>`);
continue;
}
const list=line.match(/^[-*+]\s+(.+)$/);
if(list){
if(inTaskList){result.push("</ul>");inTaskList=false;}
if(inOrderedList){result.push("</ol>");inOrderedList=false;}
if(!inUnorderedList){result.push("<ul>");inUnorderedList=true;}
result.push(`<li>${renderInline(list[1])}</li>`);
continue;
}
const ordered=line.match(/^\d+\.\s+(.+)$/);
if(ordered){
if(inTaskList){result.push("</ul>");inTaskList=false;}
if(inUnorderedList){result.push("</ul>");inUnorderedList=false;}
if(!inOrderedList){result.push("<ol>");inOrderedList=true;}
result.push(`<li>${renderInline(ordered[1])}</li>`);
continue;
}
if(inTaskList){result.push("</ul>");inTaskList=false;}
if(inUnorderedList){result.push("</ul>");inUnorderedList=false;}
if(inOrderedList){result.push("</ol>");inOrderedList=false;}
if(line.trim()){
result.push(`<p>${renderInline(line)}</p>`);
}
}
if(inTaskList)result.push("</ul>");
if(inUnorderedList)result.push("</ul>");
if(inOrderedList)result.push("</ol>");
if(inQuote){
const paragraphs=quoteContent.filter(l=>l.trim()).map(l=>`<p>${renderInline(l)}</p>`);
const content=paragraphs.join("");
result.push(`<blockquote${calloutType?` class="callout callout-${calloutType.toLowerCase()}"`:""}>${calloutTitle?`<div class="callout-title">${calloutTitle}</div>`:""}${content}</blockquote>`);
}
text=result.join("\n");
for(let i=0;i<codeBlocks.length;i++){
text=text.replace(`___CODE_BLOCK_${i}___`,codeBlocks[i]);
}
return text;
}
function escapeRemainingHtml(text){
const allowedTags=['b','i','u','s','em','strong','del','mark','sub','sup','code','pre','a','img','h1','h2','h3','h4','h5','h6','p','blockquote','ul','ol','li','br','hr'];
let result='';
let pos=0;
const tagRegex=/<(\/?)([\w]+)([^>]*)>/g;
let match;
while((match=tagRegex.exec(text))!==null){
result+=text.substring(pos,match.index).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
if(allowedTags.includes(match[2].toLowerCase())){
result+=match[0];
}else{
result+=match[0].replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
pos=tagRegex.lastIndex;
}
result+=text.substring(pos).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
return result;
}
function renderInline(text){
text=text.replace(/`([^`]+)`/g,(m,code)=>`<code>${code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</code>`);
text=text.replace(/\*\*(.+?)\*\*/g,"<b>$1</b>");
text=text.replace(/(?<!\*)\*([^\*\n]+?)\*(?!\*)/g,"<i>$1</i>");
text=text.replace(/__(.+?)__/g,"<u>$1</u>");
text=text.replace(/~~(.+?)~~/g,"<s>$1</s>");
text=text.replace(/==(.+?)==/g,"<mark>$1</mark>");
text=text.replace(/~([^\s~]+?)~/g,"<sub>$1</sub>");
text=text.replace(/\^([^\s\^]+?)\^/g,"<sup>$1</sup>");
text=text.replace(/\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)/g,(m,alt,src,href)=>`<a href="${href.replace(/"/g,'&quot;')}"><img src="${src.replace(/"/g,'&quot;')}" alt="${alt.replace(/"/g,'&quot;')}"></a>`);
text=text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g,(m,alt,src)=>`<img src="${src.replace(/"/g,'&quot;')}" alt="${alt.replace(/"/g,'&quot;')}">`);
text=text.replace(/\[([^\]]+)\]\(([^)]+)\)/g,(m,label,href)=>`<a href="${href.replace(/"/g,'&quot;')}">${label}</a>`);
text=escapeRemainingHtml(text);
return text;
}
