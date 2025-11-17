from google.adk.agents.llm_agent import Agent
from datetime import datetime
from zoneinfo import ZoneInfo
# Mock tool implementation
# def get_current_time(city: str) -> dict:
#     """Returns the current time in a specified city."""
#     return {"status": "success", "city": city, "time": "10:30 AM"}

# root_agent = Agent(
#     model='gemini-2.5-flash',
#     name='root_agent',
#     description="Tells the current time in a specified city.",
#     instruction="You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.",
#     tools=[get_current_time],
# )


def get_current_time(city: str) -> dict:
    """Returns the real current time in a specified city using built-in datetime & zoneinfo."""
    try:
        # Some common example city → timezone mappings
        city_to_timezone = {
            "new york": "America/New_York",
            "london": "Europe/London",
            "tokyo": "Asia/Tokyo",
            "paris": "Europe/Paris",
            "dubai": "Asia/Dubai",
            "sydney": "Australia/Sydney",
            "mumbai": "Asia/Kolkata",
            "ahmedabad": "Asia/Kolkata",
            "toronto": "America/Toronto",
            "los angeles": "America/Los_Angeles",
        }

        tz_name = city_to_timezone.get(city.lower())
        if not tz_name:
            return {"status": "error", "message": f"City '{city}' not recognized. Try one from the list: {list(city_to_timezone.keys())}"}

        # Get current time in that timezone
        now = datetime.now(ZoneInfo(tz_name))
        time_str = now.strftime("%I:%M %p")

        return {"status": "success", "city": city.title(), "time": time_str}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# # Mock Agent class (like in your example)
# class Agent:
#     def __init__(self, model, name, description, instruction, tools):
#         self.model = model
#         self.name = name
#         self.description = description
#         self.instruction = instruction
#         self.tools = tools

#     def use_tool(self, tool_name, *args, **kwargs):
#         for tool in self.tools:
#             if tool.__name__ == tool_name:
#                 return tool(*args, **kwargs)
#         return {"status": "error", "message": f"Tool '{tool_name}' not found."}



# Create your ADK agent
root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Tells the current time in a specified city.",
    instruction="You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.",
    tools=[get_current_time],
)
# adk web --port 8000