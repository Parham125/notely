from nanoid import generate

def generate_id():
    return generate(size=20)

def generate_session_token():
    return generate(size=30)
