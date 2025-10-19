import hashlib

def generate_avatar_svg(username,display_name):
    hash_value=int(hashlib.md5(display_name.encode()).hexdigest(),16)
    colors=["#ef4444","#f59e0b","#10b981","#3b82f6","#8b5cf6","#ec4899","#14b8a6","#f97316"]
    bg_color=colors[hash_value%len(colors)]
    text_color="#ffffff"
    initial=display_name[0].upper() if display_name else "?"
    svg=f'''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="{bg_color}"/><text x="50" y="50" font-family="Arial,sans-serif" font-size="48" font-weight="bold" fill="{text_color}" text-anchor="middle" dominant-baseline="central">{initial}</text></svg>'''
    return svg

def get_avatar_url(user):
    if user.get("profile_picture"):
        return f"/uploads/{user['profile_picture']}"
    return f"data:image/svg+xml,{generate_avatar_svg(user['username'],user['display_name']).replace('#','%23').replace('<','%3C').replace('>','%3E').replace('\"','%22')}"
