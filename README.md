
---

# **Timesheet Generator AI**

Creating timesheets in the corporate world is repetitive, boring, and time-consuming. So we built an automated **AI Timesheet Agent** that converts raw task text into a clean, structured, professional-grade timesheet — instantly.
Our agent makes daily reporting faster, smoother, and actually enjoyable using advanced LLM parsing, smart formatting, and a minimal UI.

---

## 🚀 **Build Your Own AI Agent Using This Project**

This repository contains the starter code to help you build or extend your own AI automation agent.
It includes:

* A backend agent (`agent.py`) powered by Google ADK.
* A frontend interface (`index.html`).
* Everything you need to customize, extend, or integrate into your own startup idea.

---

## 📦 **Installing Requirements**

Create and activate a virtual environment:

```bash
python -m venv venv    or    virtualenv venv
source venv/bin/activate   
```

Install all dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🧠 **Understanding the Project Structure**

Your folder should look like this:

```

    adk/
    └── my_agent/
        ├── agent.py
        ├── templates/
        │   ├── index.html
        │   └── result.html
        ├── static/ (optional for CSS/JS)
```

---

## 🔑 **Add Your API Key (.env File Required)**

Inside your project folder, create a `.env` file:

```
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=_YOUR_API_KEY_CREDENTIALS_
```

This file is essential for running the AI agent — keep it private and never commit it!

---

## ▶️ **Running the AI Agent on Localhost**

With your virtual environment activated, run the following command:

```bash
uvicorn my_agent.agent:app --reload --port 8000
```

Your AI Timesheet Agent will now be hosted at:

👉 **[http://localhost:8000]**

---

## 🖼️ **Screenshots / Images Section**

<img width="1918" height="934" alt="image" src="https://github.com/user-attachments/assets/69dc443f-1639-46f3-9ca4-18460740eed0" />
<img width="1919" height="923" alt="image" src="https://github.com/user-attachments/assets/6c86a628-ef64-4c61-99b8-af8ce7eff584" />


## 🙏 **Thank You**

Thank you for checking out this project!
Feel free to explore, improve, and use this code however you like.
Your interest and support means a lot — happy building! 🚀❤️

---

