from google.adk.agents.llm_agent import Agent
from google.adk.agents.tools import Tool
from datetime import datetime, timedelta

# For Excel/PDF
import openpyxl
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# ---------------------------
# TOOLS
# ---------------------------

def date_tool(date_str: str) -> dict:
    today = datetime.now()
    if date_str.lower() == "today":
        return {"date": today.strftime("%Y-%m-%d")}
    elif date_str.lower() == "yesterday":
        return {"date": (today - timedelta(days=1)).strftime("%Y-%m-%d")}
    return {"date": date_str}

def validation_tool(entry: dict) -> dict:
    if entry["hours"] > 24:
        return {"error": f"Invalid hours in entry: {entry}"}
    return {"status": "ok"}

date_tool_fn = Tool(function=date_tool, name="DateTool")
validation_tool_fn = Tool(function=validation_tool, name="ValidationTool")

# ---------------------------
# SUB-AGENTS
# ---------------------------

task_extractor_agent = Agent(
    model="gemini-2.0-flash",
    name="TaskExtractor",
    instructions="Extract tasks, hours, and dates from user input. Output JSON."
)

calendar_agent = Agent(
    model="gemini-2.0-flash",
    name="CalendarAgent",
    instructions="Convert relative dates to YYYY-MM-DD using DateTool.",
    tools=[date_tool_fn]
)

hours_agent = Agent(
    model="gemini-2.0-flash",
    name="HoursAgent",
    instructions="Fill missing hours with 8 and normalize hour values."
)

validator_agent = Agent(
    model="gemini-2.0-flash",
    name="ValidatorAgent",
    instructions="Check if task hours and dates are valid using ValidationTool.",
    tools=[validation_tool_fn]
)

review_agent = Agent(
    model="gemini-2.0-flash",
    name="ReviewAgent",
    instructions="Polish task descriptions to be professional and readable."
)

format_agent = Agent(
    model="gemini-2.0-flash",
    name="FormatAgent",
    instructions="Format the final tasks into a readable timesheet table."
)

# ---------------------------
# ROOT AGENT
# ---------------------------

root_agent = Agent(
    model="gemini-2.0-pro",
    name="TimesheetManager",
    instructions="""
You are the master agent orchestrating all sub-agents to generate a timesheet.
Use the following pipeline:
TaskExtractor -> CalendarAgent -> HoursAgent -> ValidatorAgent -> ReviewAgent -> FormatAgent
Always output a clean, readable timesheet.
""",
    sub_agents=[
        task_extractor_agent,
        calendar_agent,
        hours_agent,
        validator_agent,
        review_agent,
        format_agent
    ]
)

# ---------------------------
# Functions for PDF / Excel Generation
# ---------------------------

def generate_excel(tasks, filename="timesheet.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Timesheet"

    headers = ["Date", "Task", "Hours"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for t in tasks:
        ws.append([t["date"], t["task"], t["hours"]])

    wb.save(filename)
    print(f"Excel saved as {filename}")

def generate_pdf(tasks, filename="timesheet.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    data = [["Date", "Task", "Hours"]]
    for t in tasks:
        data.append([t["date"], t["task"], t["hours"]])

    table = Table(data)
    style = TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BOTTOMPADDING",(0,0),(-1,0),12),
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ])
    table.setStyle(style)
    doc.build([table])
    print(f"PDF saved as {filename}")

# ---------------------------
# TERMINAL CHATBOT LOOP
# ---------------------------

print("AI Timesheet Chatbot with Excel/PDF Generation")
print("Type 'exit' to quit.\n")

cumulative_tasks = []  # store tasks for Excel/PDF

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Exiting chatbot...")
        break

    # Run root agent
    result = root_agent.run(user_input)
    print(f"\nAI:\n{result.text}\n")

    # For PDF/Excel: parse output into structured tasks
    # Simplest way: assume agent returns list of dicts in JSON format
    try:
        import json
        tasks = json.loads(result.text)
        cumulative_tasks.extend(tasks)
        generate_excel(cumulative_tasks)
        generate_pdf(cumulative_tasks)
    except Exception as e:
        print("Could not generate Excel/PDF. Ensure agent outputs valid JSON list of tasks.")
