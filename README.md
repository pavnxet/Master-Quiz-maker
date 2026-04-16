# Quiz Master HTML 🎓

A professional-grade, bilingual quiz generation suite that transforms simple JSON data into high-performance, self-contained interactive HTML quiz applications. This project allows you to generate quizzes that work offline, support custom marking, and provide detailed analytics.

---

### 🌟 Key Features

* **Bilingual Excellence**: Simultaneous display of questions, options, and explanations in both English and Hindi.
* **Zero-Dependency Output**: The generated `.html` files are 100% self-contained, requiring no external CSS or JS libraries to function.
* **Advanced Marking System**: Supports custom positive and negative marking schemes (e.g., +1 for correct, -0.25 for wrong).
* **Interactive UI/UX**:
    * 🌗 **Dark/Light Mode**: Smooth theme toggling based on user preference.
    * ⏱️ **Timer Modes**: Supports per-question timing, custom total timers, or free-play modes.
    * 📍 **Navigator**: Integrated question navigator for quick jumping between items.
    * 📈 **Analytics**: Detailed performance statistics and session history stored in browser `localStorage`.

---

### 🚀 Usage Methods

#### 1. Python Command Line Tool
Best for local generation or automated workflows.
* **Requirements**: Python 3.x (Zero external libraries required for core generation).
* **Command**: 
    ```bash
    python quiz_generator.py <input_file.json> [output_file.html]
    ```

#### 2. Flask Web Interface
Provides a user-friendly drag-and-drop dashboard to generate quizzes in a browser.
* **Setup**: 
    ```bash
    pip install -r requirements.txt
    python app.py
    ```
* **Access**: Open `http://localhost:3000` in your browser.

#### 3. Cloudflare Worker + Telegram Bot
A serverless solution to generate quizzes via a web UI or directly through Telegram.
* **Deployment**: Update `wrangler.toml` and run `npx wrangler deploy`.
* **Bot Usage**: Send a `.json` file to your configured bot to receive a generated HTML quiz instantly.

---

### 🤖 Telegram Bot Deep Setup

To enable the Telegram Bot functionality, follow these steps:

1.  **Obtain a Token**: Message [@BotFather](https://t.me/botfather) on Telegram to create a new bot and get your `TELEGRAM_TOKEN`.
2.  **Configure Environment**:
    * Go to your **Cloudflare Dashboard** > **Workers** > **Settings** > **Variables**.
    * Add `TELEGRAM_TOKEN` as an environment variable.
3.  **Register the Webhook**:
    * Visit the setup URL once after deployment: `https://your-worker-name.your-subdomain.workers.dev/setup`.
    * The worker will automatically register itself with Telegram's API.
4.  **Start Generating**: Simply drag and drop your JSON quiz file into the chat with your bot.

---

### 📝 Input Format (JSON)

The generator expects a JSON array of objects with the following structure:

```json
[
  {
    "qEnglish": "What is the capital of France?",
    "qHindi": "फ्रांस की राजधानी क्या है?",
    "optionsEnglish": ["London", "Paris", "Berlin", "Madrid"],
    "optionsHindi": ["लंदन", "पेरिस", "बर्लिन", "मैड्रिड"],
    "correct": 1,
    "explanationEnglish": "Paris is the capital of France.",
    "explanationHindi": "पेरिस फ्रांस की राजधानी है।",
    "subject": "Geography",
    "topic": "Capitals"
  }
]
```

---

### 🛠️ Tech Stack

* **Core Logic**: Python 3.x, JavaScript (ES6+).
* **Web Framework**: Flask.
* **Serverless**: Cloudflare Workers API.
* **Styling**: Modern CSS3 with CSS Variables for theme management.

---

### 📄 License
This project is licensed under the **MIT License**.
