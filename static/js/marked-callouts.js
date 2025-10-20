const calloutExtension={
name:"callouts",
level:"block",
start(src){return src.match(/^>\s*\[!/m)?.index;},
tokenizer(src){
const match=src.match(/^((?:>\s*\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\].*\n)+(?:>\s*.*\n)*)/);
if(!match)return;
const text=match[1];
const lines=text.split("\n").filter(l=>l.trim());
const firstLine=lines[0];
const typeMatch=firstLine.match(/^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$/);
if(!typeMatch)return;
const type=typeMatch[1];
const title=typeMatch[2].trim()||type;
const content=lines.slice(1).map(l=>l.replace(/^>\s*/,"")).join("\n");
return{
type:"callouts",
raw:match[0],
calloutType:type,
title:title,
text:content,
tokens:this.lexer.blockTokens(content)
};
},
renderer(token){
const typeClass=token.calloutType.toLowerCase();
const content=this.parser.parse(token.tokens);
return`<blockquote class="callout callout-${typeClass}"><div class="callout-title">${token.title}</div>${content}</blockquote>\n`;
}
};
