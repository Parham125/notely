# Notely

A self-hosted, open-source blog platform built with Flask that lets you create and share blog posts with markdown support.

## Features

- **User Authentication**: Signup and signin without captcha
- **User Profiles**: Each user has a profile with username, display name, and profile picture (max 8MB)
- **Blog Creation**: Write blogs with full markdown support (17 features)
- **Draft System**: Save blogs as drafts before publishing
- **Comments**: Nested comment system with replies
- **Search**: Search blogs by title and content
- **Dark Mode**: Toggle between light and dark themes
- **Session Management**: View and manage active sessions across devices
- **Responsive Design**: Mobile-first responsive UI

## Markdown Support

Notely supports 17 markdown features:

1. Headings (H1-H6)
2. Bold (`**text**` or `__text__`)
3. Italic (`*text*`)
4. Italic alternate (`_text_`)
5. Blockquote (`> text`)
6. Ordered lists
7. Unordered lists
8. Inline code
9. Links
10. Linked images
11. Custom images
12. Fenced code blocks with syntax highlighting
13. Strikethrough (`~~text~~`)
14. Task lists
15. Highlight (`==text==`)
16. Subscript (`~text~`)
17. Superscript (`^text^`)

## Installation

### Local Development

1. Clone the repository
2. Install dependencies:
```bash
python3.13 -m pip install -r requirements.txt
```

3. Run the application:
```bash
python3.13 main.py
```

4. Open your browser to `http://localhost:4782`

### Docker Compose

1. Clone the repository
2. Run with Docker Compose:
```bash
docker-compose up
```

3. Open your browser to `http://localhost:4782`

The application will automatically create the SQLite database and upload directory on first run. Data persists in the `data/` volume.

## Tech Stack

- **Backend**: Flask
- **Server**: Waitress
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Markdown**: Custom parser
- **Authentication**: Custom session system with bcrypt

## Security Features

- Custom session management (no reliance on Flask sessions)
- Password hashing with bcrypt
- Session tracking with browser and device information
- Chunked file upload validation
- XSS prevention in markdown rendering
- SQL injection prevention with parameterized queries

## License

MIT License - See LICENSE file for details

## Contributing

This is an open-source project. Contributions are welcome!
