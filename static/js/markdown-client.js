function renderMarkdownClient(text){
if(!text)return"";
text=sanitizeHtml(text);
const codeBlocks=[];
text=text.replace(/```(\w+)?\n(.*?)```/gs,(m,lang,code)=>{
const html=`<pre><code class="language-${(lang||"").replace(/[<>"]/g,"")}${code.replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/&/g,"&amp;")}</code></pre>`;
codeBlocks.push(html);
return`___CODE_BLOCK_${codeBlocks.length-1}___`;
});
const lines=text.split("\n");
let result=[];
let inQuote=false;
let quoteContent=[];
let calloutType=null;
for(let i=0;i<lines.length;i++){
const line=lines[i];
const calloutMatch=line.match(/^>\s*\[!(IMPORTANT|WARNING|NOTE|ERROR)\]\s*(.*)$/);
if(calloutMatch){
if(inQuote&&calloutType!==calloutMatch[1]){
result.push(`<blockquote class="callout callout-${calloutType.toLowerCase()}">${quoteContent.map(c=>renderInline(c)).join(" ")}</blockquote>`);
quoteContent=[];
}
calloutType=calloutMatch[1];
inQuote=true;
quoteContent.push(calloutMatch[2]);
continue;
}
const quoteMatch=line.match(/^>\s*(.*)$/);
if(quoteMatch){
if(!inQuote)inQuote=true;
quoteContent.push(quoteMatch[1]);
continue;
}
if(inQuote){
result.push(`<blockquote${calloutType?` class="callout callout-${calloutType.toLowerCase()}"`:""}>${quoteContent.map(c=>renderInline(c)).join(" ")}</blockquote>`);
quoteContent=[];
inQuote=false;
calloutType=null;
}
const heading=line.match(/^(#{1,6})\s+(.+)$/);
if(heading){
result.push(`<h${heading[1].length}>${renderInline(heading[2])}</h${heading[1].length}>`);
continue;
}
const task=line.match(/^[-*+]\s+\[([ xX])\]\s+(.+)$/);
if(task){
const checked=task[1].toLowerCase()==="x"?"checked":"";
result.push(`<li><input type="checkbox" ${checked} disabled>${renderInline(task[2])}</li>`);
continue;
}
const list=line.match(/^[-*+]\s+(.+)$/);
if(list){
result.push(`<li>${renderInline(list[1])}</li>`);
continue;
}
const ordered=line.match(/^\d+\.\s+(.+)$/);
if(ordered){
result.push(`<li>${renderInline(ordered[1])}</li>`);
continue;
}
if(line.trim()){
result.push(`<p>${renderInline(line)}</p>`);
}
}
if(inQuote){
result.push(`<blockquote${calloutType?` class="callout callout-${calloutType.toLowerCase()}"`:""}>${quoteContent.map(c=>renderInline(c)).join(" ")}</blockquote>`);
}
text=result.join("\n");
for(let i=0;i<codeBlocks.length;i++){
text=text.replace(`___CODE_BLOCK_${i}___`,codeBlocks[i]);
}
return text;
}
function sanitizeHtml(text){
return text.replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/&(?!lt;|gt;|amp;)/g,"&amp;").replace(/javascript:/gi,"").replace(/<script[^>]*>[\s\S]*?<\/script>/gi,"").replace(/on\w+\s*=/gi,"");
}
function renderInline(text){
text=text.replace(/`([^`]+)`/g,"<code>$1</code>");
text=text.replace(/\*\*(.+?)\*\*/g,"<b>$1</b>");
text=text.replace(/(?<!\*)\*([^\*\n]+?)\*(?!\*)/g,"<i>$1</i>");
text=text.replace(/(?<!_)_([^_\n]+?)_(?!_)/g,"<u>$1</u>");
text=text.replace(/~~(.+?)~~/g,"<s>$1</s>");
text=text.replace(/==(.+?)==/g,"<mark>$1</mark>");
text=text.replace(/~([^\s~]+?)~/g,"<sub>$1</sub>");
text=text.replace(/\^([^\s\^]+?)\^/g,"<sup>$1</sup>");
text=text.replace(/\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)/g,'<a href="$3"><img src="$2" alt="$1"></a>');
text=text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g,'<img src="$2" alt="$1">');
text=text.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2">$1</a>');
return text;
}
