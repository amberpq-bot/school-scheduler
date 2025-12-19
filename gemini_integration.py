import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
import os

# Initialize Vertex AI
# We assume the environment has GOOGLE_APPLICATION_CREDENTIALS or is running in a GCP environment
# User might need to set project/location if not auto-detected
try:
    vertexai.init() 
except Exception as e:
    print(f"Warning: Vertex AI init failed (might be expected if credentials not set yet): {e}")

def parse_scheduler_command(text: str) -> dict:
    """
    Parses natural language text to extract scheduler data.
    Returns a dict with 'type' (teacher, room, class) and 'data' (dict of attributes).
    """
    model = GenerativeModel("gemini-1.5-flash-001")
    
    prompt = f"""
    You are a data extraction assistant for a school scheduling app.
    Extract the following entities from the text: Teacher, Room, or Class.
    
    Output JSON ONLY with this structure:
    {{
        "type": "teacher" | "room" | "class",
        "data": {{ ...attributes... }}
    }}
    
    Attributes for Teacher: name, qualifications (list of strings).
    Attributes for Room: name, capacity (int).
    Attributes for Class: name, subject, elementary_sessions (int, default 1), preferred_teacher_name (optional).
    
    Example Input: "Add Mr. Smith who teaches Math and Physics"
    Example Output: {{ "type": "teacher", "data": {{ "name": "Mr. Smith", "qualifications": ["Math", "Physics"] }} }}
    
    Example Input: "Create a room called Room 101 with 30 seats"
    Example Output: {{ "type": "room", "data": {{ "name": "Room 101", "capacity": 30 }} }}

    Example Input: "Math 101 class for Math subject needs 3 sessions"
    Example Output: {{ "type": "class", "data": {{ "name": "Math 101", "subject": "Math", "required_sessions": 3 }} }}

    Text to parse: "{text}"
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean response to ensure pure JSON
        content = response.text.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}

def analyze_schedule_insights(schedule_data: str) -> str:
    """
    Analyzes the textual representation of a schedule to provide insights.
    """
    model = GenerativeModel("gemini-1.5-flash-001")
    
    prompt = f"""
    You are a helpful assistant analyzing a school timetable.
    Here is the generated schedule data:
    {schedule_data}
    
    Please provide a brief, friendly summary of this schedule. 
    Highlight how many classes each teacher has, room utilization, and any potential improvements or balanced workload observations.
    Keep it concise (3-4 bullet points).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not generate insights: {str(e)}"
