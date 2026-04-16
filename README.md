# Quiz Master HTML 🎓

A powerful, bilingual (English + Hindi) quiz generator that creates self-contained interactive HTML quiz pages from simple JSON/TXT input.

## Features

- **Bilingual Support**: Display questions and options in both English and Hindi simultaneously.
- **Offline Ready**: The generated `.html` quiz is 100% self-contained and works offline.
- **Interactive UI**:
  - Dark/Light mode toggle.
  - Custom marking scheme (positive and negative marking).
  - Built-in timer (optional).
  - Detailed performance statistics and session history (stored in browser `localStorage`).
  - Question navigator for easy jumping.
  - Explanations shown after answering.

## 🚀 Ways to Use

### 1. Python Command Line Tool
Perfect for local generation.

**Requirements**: Python 3.x (no external libraries needed)

**Usage**:
```bash
python quiz_generator.py <input_file.json> [output_file.html]
```

### 2. Flask Web App
A simple web interface to upload files and download the generated quiz.

**Requirements**: Python 3.x + Flask
```bash
pip install -r requirements.txt
python app.py
```
Then visit `http://localhost:3000`.

### 3. Cloudflare Worker + Telegram Bot
Deploy as a serverless tool or use it via Telegram.

- **Web interface**: Serves a drag-and-drop upload UI.
- **Telegram Bot**: Send a `.json` file to the bot and it returns the HTML quiz instantly.

**Deployment**:
Update `wrangler.toml` and run:
```bash
npx wrangler deploy
```

## 📝 Input Format (JSON)

```json
[
  {
    "qEnglish": "What is the capital of France?",
    "qHindi": "फ्रांस की राजधानी क्या है?",
    "optionsEnglish": ["London", "Paris", "Berlin", "Madrid"],
    "optionsHindi": ["लंदन", "पेरिस", "बर्लिन", "मैड्रिड"],
    "correct": 1,
    "explanationEnglish": "Paris is the capital and largest city of France.",
    "explanationHindi": "पेरिस फ्रांस की राजधानी और सबसे बड़ा शहर है।",
    "subject": "General Knowledge",
    "topic": "Geography"
  }
]
```

## License
MIT
