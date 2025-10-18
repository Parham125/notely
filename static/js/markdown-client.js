function renderMarkdownClient(text){
if(!text)return"";
text=sanitizeHtml(text);
const codeBlocks=[];
text=text.replace(/```(\w+)?\n(.*?)```/gs,(m,lang,code)=>{
const html=`<pre><code class="language-${(lang||"").replace(/[<>"]/g,"")}${code.replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/&/g,"&amp;")}</code></pre>`;
codeBlocks.push(html);
return`___CODE_BLOCK_${codeBlocks.length-1}___`;
});
text=text.split("\n").map(line=>{
const heading=line.match(/^(#{1,6})\s+(.+)$/);
if(heading){
const level=heading[1].length;
return`<h${level}>${renderInline(heading[2])}</h${level}>`;
}
const task=line.match(/^[-*+]\s+\[([ xX])\]\s+(.+)$/);
if(task){
const checked=task[1].toLowerCase()==="x"?"checked":"";
return`<li><input type="checkbox" ${checked} disabled>${renderInline(task[2])}</li>`;
}
const list=line.match(/^[-*+]\s+(.+)$/);
if(list)return`<li>${renderInline(list[1])}</li>`;
const ordered=line.match(/^\d+\.\s+(.+)$/);
if(ordered)return`<li>${renderInline(ordered[1])}</li>`;
const quote=line.match(/^>\s*(.*)$/);
if(quote)return`<blockquote>${renderInline(quote[1])}</blockquote>`;
if(line.trim())return`<p>${renderInline(line)}</p>`;
return"";
}).join("\n");
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
text=text.replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>");
text=text.replace(/__(.+?)__/g,"<strong>$1</strong>");
text=text.replace(/(?<!\*)\*([^\*\n]+?)\*(?!\*)/g,"<em>$1</em>");
text=text.replace(/(?<!_)_([^_\n]+?)_(?!_)/g,"<em>$1</em>");
text=text.replace(/~~(.+?)~~/g,"<del>$1</del>");
text=text.replace(/==(.+?)==/g,"<mark>$1</mark>");
text=text.replace(/~([^\s~]+?)~/g,"<sub>$1</sub>");
text=text.replace(/\^([^\s\^]+?)\^/g,"<sup>$1</sup>");
text=text.replace(/\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)/g,'<a href="$3"><img src="$2" alt="$1"></a>');
text=text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g,'<img src="$2" alt="$1">');
text=text.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2">$1</a>');
return text;
}
