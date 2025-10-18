import re
import html as html_module

def sanitize_html(text):
    text=html_module.escape(text)
    dangerous_patterns=[r"<script.*?>.*?</script>",r"<iframe.*?>.*?</iframe>",r"<object.*?>.*?</object>",r"<embed.*?>",r"<applet.*?>.*?</applet>",r"javascript:",r"on\w+\s*="]
    for pattern in dangerous_patterns:
        text=re.sub(pattern,"",text,flags=re.IGNORECASE|re.DOTALL)
    return text

def parse_fenced_code_blocks(text):
    code_blocks=[]
    def placeholder(match):
        lang=match.group(1) or ""
        code=match.group(2).rstrip("\n")
        escaped_code=html_module.escape(code)
        if lang:
            html_code=f'<pre><code class="language-{html_module.escape(lang)}">{escaped_code}</code></pre>'
        else:
            html_code=f"<pre><code>{escaped_code}</code></pre>"
        code_blocks.append(html_code)
        return f"___CODE_BLOCK_{len(code_blocks)-1}___"
    text=re.sub(r"```(\w+)?\n(.*?)```",placeholder,text,flags=re.DOTALL)
    return text,code_blocks

def restore_code_blocks(text,code_blocks):
    for i,block in enumerate(code_blocks):
        text=text.replace(f"___CODE_BLOCK_{i}___",block)
    return text

def parse_inline_code(text):
    return re.sub(r"`([^`]+)`",lambda m: f"<code>{html_module.escape(m.group(1))}</code>",text)

def parse_bold(text):
    text=re.sub(r"\*\*(.+?)\*\*",r"<b>\1</b>",text)
    return text

def parse_italic(text):
    text=re.sub(r"(?<!\*)\*([^\*\n]+?)\*(?!\*)",r"<i>\1</i>",text)
    text=re.sub(r"(?<![_\w])_([^_\n]+?)_(?![_\w])",r"<i>\1</i>",text)
    return text

def parse_strikethrough(text):
    return re.sub(r"~~(.+?)~~",r"<s>\1</s>",text)

def parse_highlight(text):
    return re.sub(r"==(.+?)==",r"<mark>\1</mark>",text)

def parse_underline(text):
    return re.sub(r"__(.+?)__",r"<u>\1</u>",text)

def parse_subscript(text):
    return re.sub(r"~([^~\s]+?)~",r"<sub>\1</sub>",text)

def parse_superscript(text):
    return re.sub(r"\^([^\^\s]+?)\^",r"<sup>\1</sup>",text)

def parse_linked_images(text):
    return re.sub(r"\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)",lambda m: f'<a href="{html_module.escape(m.group(3))}"><img src="{html_module.escape(m.group(2))}" alt="{html_module.escape(m.group(1))}"></a>',text)

def parse_images(text):
    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",lambda m: f'<img src="{html_module.escape(m.group(2))}" alt="{html_module.escape(m.group(1))}">',text)

def parse_links(text):
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)",lambda m: f'<a href="{html_module.escape(m.group(2))}">{m.group(1)}</a>',text)

def parse_inline_elements(text):
    text=parse_inline_code(text)
    text=parse_bold(text)
    text=parse_italic(text)
    text=parse_underline(text)
    text=parse_strikethrough(text)
    text=parse_highlight(text)
    text=parse_subscript(text)
    text=parse_superscript(text)
    text=parse_linked_images(text)
    text=parse_images(text)
    text=parse_links(text)
    return text

def parse_headings(text):
    lines=text.split("\n")
    result=[]
    for line in lines:
        match=re.match(r"^(#{1,6})\s+(.+)$",line)
        if match:
            level=len(match.group(1))
            content=match.group(2)
            result.append(f"<h{level}>{parse_inline_elements(content)}</h{level}>")
        else:
            result.append(line)
    return "\n".join(result)

def parse_task_lists(text):
    lines=text.split("\n")
    result=[]
    in_list=False
    for line in lines:
        match=re.match(r"^[-*+]\s+\[([ xX])\]\s+(.+)$",line)
        if match:
            if not in_list:
                result.append("<ul class=\"task-list\">")
                in_list=True
            checked="checked" if match.group(1).lower()=="x" else ""
            content=match.group(2)
            result.append(f'<li><input type="checkbox" {checked} disabled>{parse_inline_elements(content)}</li>')
        else:
            if in_list:
                result.append("</ul>")
                in_list=False
            result.append(line)
    if in_list:
        result.append("</ul>")
    return "\n".join(result)

def parse_unordered_lists(text):
    lines=text.split("\n")
    result=[]
    in_list=False
    for line in lines:
        match=re.match(r"^[-*+]\s+(.+)$",line)
        if match and not re.match(r"^[-*+]\s+\[",line):
            if not in_list:
                result.append("<ul>")
                in_list=True
            content=match.group(1)
            result.append(f"<li>{parse_inline_elements(content)}</li>")
        else:
            if in_list:
                result.append("</ul>")
                in_list=False
            result.append(line)
    if in_list:
        result.append("</ul>")
    return "\n".join(result)

def parse_ordered_lists(text):
    lines=text.split("\n")
    result=[]
    in_list=False
    for line in lines:
        match=re.match(r"^\d+\.\s+(.+)$",line)
        if match:
            if not in_list:
                result.append("<ol>")
                in_list=True
            content=match.group(1)
            result.append(f"<li>{parse_inline_elements(content)}</li>")
        else:
            if in_list:
                result.append("</ol>")
                in_list=False
            result.append(line)
    if in_list:
        result.append("</ol>")
    return "\n".join(result)

def parse_blockquotes(text):
    lines=text.split("\n")
    result=[]
    in_blockquote=False
    blockquote_content=[]
    callout_type=None
    for line in lines:
        match=re.match(r"^>\s*\[!(IMPORTANT|WARNING|NOTE|ERROR)\]\s*(.*)$",line)
        if match:
            if in_blockquote and callout_type!=match.group(1):
                content="\n".join(blockquote_content)
                result.append(f"<blockquote class=\"callout callout-{callout_type.lower()}\">{parse_inline_elements(content)}</blockquote>")
                blockquote_content=[]
            callout_type=match.group(1)
            in_blockquote=True
            blockquote_content.append(match.group(2))
            continue
        match=re.match(r"^>\s*(.*)$",line)
        if match:
            if not in_blockquote:
                in_blockquote=True
            blockquote_content.append(match.group(1))
        else:
            if in_blockquote:
                content="\n".join(blockquote_content)
                if callout_type:
                    result.append(f"<blockquote class=\"callout callout-{callout_type.lower()}\">{parse_inline_elements(content)}</blockquote>")
                else:
                    result.append(f"<blockquote>{parse_inline_elements(content)}</blockquote>")
                blockquote_content=[]
                in_blockquote=False
                callout_type=None
            result.append(line)
    if in_blockquote:
        content="\n".join(blockquote_content)
        if callout_type:
            result.append(f"<blockquote class=\"callout callout-{callout_type.lower()}\">{parse_inline_elements(content)}</blockquote>")
        else:
            result.append(f"<blockquote>{parse_inline_elements(content)}</blockquote>")
    return "\n".join(result)

def parse_paragraphs(text):
    lines=text.split("\n")
    result=[]
    paragraph_lines=[]
    for line in lines:
        stripped=line.strip()
        if stripped and not stripped.startswith("<"):
            paragraph_lines.append(line)
        else:
            if paragraph_lines:
                content=" ".join(paragraph_lines)
                result.append(f"<p>{parse_inline_elements(content)}</p>")
                paragraph_lines=[]
            if stripped:
                result.append(line)
    if paragraph_lines:
        content=" ".join(paragraph_lines)
        result.append(f"<p>{parse_inline_elements(content)}</p>")
    return "\n".join(result)

def render_markdown(text):
    if not text:
        return ""
    text=sanitize_html(text)
    text,code_blocks=parse_fenced_code_blocks(text)
    text=parse_headings(text)
    text=parse_blockquotes(text)
    text=parse_task_lists(text)
    text=parse_unordered_lists(text)
    text=parse_ordered_lists(text)
    text=parse_paragraphs(text)
    text=restore_code_blocks(text,code_blocks)
    return text
