import os
import json
import re
import pandas as pd
from datetime import datetime, timedelta
import dateparser
from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from google.adk.agents.llm_agent import Agent

# ====================== Templates setup ======================
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# ====================== FastAPI app ==========================
app = FastAPI()

# ====================== GREETING DETECTOR ===================
GREETINGS = {"hi", "hello", "hey", "yo", "good morning", "good evening", "good afternoon", "sup", "hola"}
def is_greeting(text: str) -> bool:
    text = text.lower().strip()
    return any(text.startswith(g) for g in GREETINGS)

# ====================== TASK PARSING ========================
DATE_REGEX = r"""
    \b(?:last|next|previous)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b |
    \b(?:today|yesterday|tomorrow)\b |
    \b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b |
    \b\d{4}-\d{1,2}-\d{1,2}\b
"""
HOUR_REGEX = r"\b(\d+)\s*(?:h|hr|hrs|hour|hours)\b"

def parse_tasks(text: str) -> list:
    tasks = []
    parts = re.split(r',| and ', text)
    for raw in parts:
        raw = raw.strip()
        hr_m = re.search(HOUR_REGEX, raw, flags=re.IGNORECASE)
        raw_hours = hr_m.group(1) if hr_m else None
        date_m = re.search(DATE_REGEX, raw, flags=re.IGNORECASE | re.VERBOSE)
        raw_date = date_m.group(0) if date_m else None

        task_text = raw
        if hr_m:
            task_text = task_text.replace(hr_m.group(0), "")
        if raw_date:
            task_text = re.sub(re.escape(raw_date), "", task_text, flags=re.IGNORECASE)
        task_text = re.sub(r"\b(on|for|at|the|a)\b", "", task_text, flags=re.IGNORECASE)
        task_text = " ".join(task_text.split()).strip()

        tasks.append({
            "task": task_text.capitalize() if task_text else "Task",
            "raw_hours": raw_hours,
            "raw_date": raw_date
        })
    return tasks

# ====================== HOURS & DATE ========================
def parse_hours(raw_hours: str):
    return int(raw_hours) if raw_hours else 8

WEEKDAYS = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6
}

def parse_date(raw_date: str):
    if not raw_date:
        return datetime.now().strftime("%Y-%m-%d")
    
    raw_date = raw_date.lower().strip()
    parsed = dateparser.parse(
        raw_date,
        settings={'PREFER_DATES_FROM': 'past', 'RELATIVE_BASE': datetime.now(), 'STRICT_PARSING': True},
        languages=['en']
    )
    if parsed:
        return parsed.strftime("%Y-%m-%d")

    match = re.match(r'(last|next)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', raw_date)
    if match:
        which, day = match.groups()
        today = datetime.now()
        target_weekday = WEEKDAYS[day]
        current_weekday = today.weekday()
        if which == 'last':
            days_ago = (current_weekday - target_weekday) % 7
            days_ago = 7 if days_ago == 0 else days_ago
            result = today - timedelta(days=days_ago)
        else:
            days_ahead = (target_weekday - current_weekday) % 7
            days_ahead = 7 if days_ahead == 0 else days_ahead
            result = today + timedelta(days_ahead)
        return result.strftime("%Y-%m-%d")
    
    return datetime.now().strftime("%Y-%m-%d")

# ====================== PIPELINE ============================
def process_tasks(text: str):
    raw_tasks = parse_tasks(text)
    final_tasks = []
    for t in raw_tasks:
        final_tasks.append({
            "task": t["task"],
            "hours": parse_hours(t["raw_hours"]),
            "date": parse_date(t["raw_date"])
        })
    return final_tasks

#==============================================================
#                         SUB-AGENTS
#==============================================================
# 1️⃣ TaskExtractor: uses parse_tasks
task_extractor_agent = Agent(
    model="gemini-2.5-flash",
    name="TaskExtractor",
    description="Extracts raw tasks, hours, and dates from user input.",
    tools=[parse_tasks],
    instruction="Use parse_tasks(text) to extract tasks with raw_hours and raw_date.")
# 2️⃣ CalendarAgent: uses parse_date
calendar_agent = Agent(
    model="gemini-2.5-flash",
    name="CalendarAgent",
    description="Resolves raw dates into actual dates.",
    tools=[parse_date],
    instruction="For each task, convert raw_date into YYYY-MM-DD using parse_date(raw_date)."
)
# 3️⃣ HoursAgent: uses parse_hours
hours_agent = Agent(
    model="gemini-2.5-flash",
    name="HoursAgent",
    description="Converts raw_hours to integer hours.",
    tools=[parse_hours],
    instruction="For each task, convert raw_hours to integer using parse_hours(raw_hours)."
)
# -------------------------------
#        ROOT AGENT
# -------------------------------
root_agent = Agent(
    model="gemini-2.5-flash",
    name="TimesheetMaster",
    description="Master agent orchestrating all sub-agents.",
    instruction="""
You take user input and generate a timesheet.
Pipeline you MUST follow:
1. Send input to TaskExtractor
2. Send output to CalendarAgent
3. Send output to HoursAgent


Return a final formatted table.
""",
    sub_agents=[
        task_extractor_agent,
        calendar_agent,
        hours_agent,
           ]
)

# ====================== ROUTES ==============================

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "greeting": False,
            "message": None,
            "tasks": None,
            "filename": None
        }
    )


@app.post("/generate_timesheet")
def generate_timesheet(
    request: Request,
    user_input: str = Form(...),
    action: str = Form(...)
):
    # ==================== CHAT MODE ====================
    if action == "chat":

        text = user_input.lower()

        # Detect if user wrote tasks but clicked "Send Message"
        
        # Handle greetings
        if is_greeting(user_input):
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "greeting": True,
                    "message": f"{user_input.capitalize()}! How can I help you today?",
                    "tasks": None,
                    "filename": None
                }
            )
        if any(word in text for word in ["hour", "hours", "hr", "hrs", "h"]):
                    return templates.TemplateResponse(
                        "index.html",
                        {
                            "request": request,
                            "greeting": True,
                            "message": "It looks like you're entering tasks. Please click on the Generate Timesheet button.",
                            "tasks": None,
                            "filename": None
                        }
                    )

                # Default chat response
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "greeting": True,
                "message": f"I didn't quite get that. Could you please specify the tasks you worked on so I can help you generate a timesheet?",
                "tasks": None,
                "filename": None
            }
        )

    # ==================== TIMESHEET MODE ====================
    if action == "timesheet":

        tasks = process_tasks(user_input)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"timesheet_{timestamp}.xlsx"

        df = pd.DataFrame(tasks)[['date', 'task', 'hours']]

        # ---- SAVE EXCEL FOR DOWNLOAD ----
        df.to_excel(filename, index=False)

        # ---- CONVERT TO HTML FOR DISPLAY ----
        html_table = df.to_html(index=False)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "greeting": True,
                "message": f"You said: {user_input}",
                "tasks":  html_table,
                "filename": filename,
                "user_input": user_input,
                "action": action
            }
        )


@app.get("/download/{filename}")
def download_file(filename: str):
    return FileResponse(
        path=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )
