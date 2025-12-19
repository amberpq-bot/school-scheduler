import streamlit as st
import pandas as pd
from models import Teacher, Room, SchoolClass, TimeSlot
from solver import SchoolScheduler
import uuid

st.set_page_config(page_title="School Scheduler Agent", layout="wide")

# Initialize Session State
if 'teachers' not in st.session_state:
    st.session_state.teachers = []
if 'rooms' not in st.session_state:
    st.session_state.rooms = []
if 'classes' not in st.session_state:
    st.session_state.classes = []
if 'schedule' not in st.session_state:
    st.session_state.schedule = []

def generate_uid():
    return str(uuid.uuid4())[:8]

# --- Sidebar: Data Entry ---
st.sidebar.title("Configuration")

# Smart Assistant (Gemini)
from gemini_integration import parse_scheduler_command
st.sidebar.header("✨ Smart Assistant")
with st.sidebar.expander("Natural Language Input", expanded=True):
    nl_input = st.text_area("e.g. 'Add Ms. Davis for Biology'")
    if st.button("Process with Gemini"):
        if nl_input:
            with st.spinner("Asking Gemini..."):
                result = parse_scheduler_command(nl_input)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                dtype = result.get("type")
                data = result.get("data", {})
                
                if dtype == "teacher":
                    st.session_state.teachers.append(Teacher(
                        id=generate_uid(), 
                        name=data.get("name", "Unknown"), 
                        qualifications=data.get("qualifications", [])
                    ))
                    st.success(f"Added Teacher: {data.get('name')}")
                elif dtype == "room":
                    st.session_state.rooms.append(Room(
                        id=generate_uid(), 
                        name=data.get("name", "Unknown"), 
                        capacity=data.get("capacity", 30)
                    ))
                    st.success(f"Added Room: {data.get('name')}")
                elif dtype == "class":
                    # Handle preferred teacher mapping if present
                    t_id = None
                    if "preferred_teacher_name" in data:
                        t_name = data["preferred_teacher_name"]
                        # Try to find existing teacher
                        for t in st.session_state.teachers:
                            if t.name.lower() == t_name.lower():
                                t_id = t.id
                                break
                    
                    st.session_state.classes.append(SchoolClass(
                        id=generate_uid(),
                        name=data.get("name", "Unknown"),
                        subject=data.get("subject", "General"),
                        required_sessions=data.get("required_sessions", 1),
                        teacher_id=t_id
                    ))
                    st.success(f"Added Class: {data.get('name')}")
                else:
                    st.warning(f"Unknown type: {dtype}")

# Teachers Management
st.sidebar.header("1. Teachers")
with st.sidebar.expander("Add Teacher", expanded=False):
    t_name = st.text_input("Name", key="t_name")
    t_subjects = st.text_input("Subjects (comma sep)", key="t_subs")
    if st.button("Add Teacher"):
        if t_name and t_subjects:
            subjects = [s.strip() for s in t_subjects.split(',')]
            st.session_state.teachers.append(Teacher(id=generate_uid(), name=t_name, qualifications=subjects))
            st.success(f"Added {t_name}")

# Rooms Management
st.sidebar.header("2. Rooms")
with st.sidebar.expander("Add Room", expanded=False):
    r_name = st.text_input("Room Name", key="r_name")
    r_cap = st.number_input("Capacity", min_value=1, value=30, key="r_cap")
    if st.button("Add Room"):
        if r_name:
            st.session_state.rooms.append(Room(id=generate_uid(), name=r_name, capacity=r_cap))
            st.success(f"Added {r_name}")

# Classes Management
st.sidebar.header("3. Classes")
with st.sidebar.expander("Add Class", expanded=False):
    c_name = st.text_input("Class Name", key="c_name")
    c_subject = st.text_input("Subject", key="c_sub")
    c_sessions = st.number_input("Sessions/Week", min_value=1, value=3, key="c_sess")
    
    # Optional: Pre-assign teacher
    teacher_options = {t.name: t.id for t in st.session_state.teachers}
    selected_teacher_name = st.selectbox("Preferred Teacher (Optional)", ["Any"] + list(teacher_options.keys()))
    selected_teacher_id = teacher_options[selected_teacher_name] if selected_teacher_name != "Any" else None

    if st.button("Add Class"):
        if c_name and c_subject:
            st.session_state.classes.append(SchoolClass(
                id=generate_uid(), 
                name=c_name, 
                subject=c_subject, 
                required_sessions=c_sessions,
                teacher_id=selected_teacher_id
            ))
            st.success(f"Added {c_name}")

# --- Main Page ---
st.title("School Timetable Scheduler")

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Teachers")
    if st.session_state.teachers:
        df_t = pd.DataFrame([vars(t) for t in st.session_state.teachers])
        st.dataframe(df_t, use_container_width=True)
    else:
        st.info("No teachers added.")

with col2:
    st.subheader("Rooms")
    if st.session_state.rooms:
        df_r = pd.DataFrame([vars(r) for r in st.session_state.rooms])
        st.dataframe(df_r, use_container_width=True)
    else:
        st.info("No rooms added.")

with col3:
    st.subheader("Classes")
    if st.session_state.classes:
        # Convert to dict but handle optional fields for display
        data = []
        for c in st.session_state.classes:
            d = vars(c).copy()
            # Map teacher ID back to name for display
            if d['teacher_id']:
                t = next((t for t in st.session_state.teachers if t.id == d['teacher_id']), None)
                d['teacher_name'] = t.name if t else "Unknown"
            else:
                d['teacher_name'] = "Any"
            data.append(d)
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No classes added.")

st.markdown("---")

# Generate Button
if st.button("Generate Schedule", type="primary"):
    if not st.session_state.teachers or not st.session_state.rooms or not st.session_state.classes:
        st.error("Please add at least one teacher, room, and class.")
    else:
        # Define Time Slots (Fixed for Demo: Mon-Fri, 5 periods)
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        time_slots = []
        for d in days:
            for p in range(1, 6):
                time_slots.append(TimeSlot(id=f"{d}_{p}", day=d, period=p))
        
        with st.spinner("Optimizing Schedule..."):
            scheduler = SchoolScheduler(
                st.session_state.teachers, 
                st.session_state.rooms, 
                st.session_state.classes, 
                time_slots
            )
            response = scheduler.solve()
        
        if response.status in ["OPTIMAL", "FEASIBLE"]:
            st.success(f"Schedule Found! Status: {response.status}")
            
            # Process results for display
            schedule_data = []
            for item in response.schedule:
                # Lookup objects
                cls = next((c for c in st.session_state.classes if c.id == item.class_id), None)
                tch = next((t for t in st.session_state.teachers if t.id == item.teacher_id), None)
                rm = next((r for r in st.session_state.rooms if r.id == item.room_id), None)
                slot = next((s for s in time_slots if s.id == item.time_slot_id), None)
                
                if cls and tch and rm and slot:
                    schedule_data.append({
                        "Day": slot.day,
                        "Period": slot.period,
                        "Class": cls.name,
                        "Subject": cls.subject,
                        "Teacher": tch.name,
                        "Room": rm.name
                    })
            
            df_schedule = pd.DataFrame(schedule_data)
            
            # Pivot for grid view (optional) - let's verify list view first
            st.subheader("Schedule List")
            st.dataframe(df_schedule, use_container_width=True)
            
            # Grid View
            st.subheader("Timetable Grid")
            if not df_schedule.empty:
                pivot = df_schedule.pivot(index='Period', columns='Day', values='Class')
                st.dataframe(pivot, use_container_width=True)

            # Gemini Insights
            from gemini_integration import analyze_schedule_insights
            st.markdown("---")
            st.subheader("✨ Gemini Insights")
            if st.button("Analyze with Gemini"):
                with st.spinner("Gemini is analyzing the schedule..."):
                    # Convert dataframe to string for context
                    csv_data = df_schedule.to_csv(index=False)
                    insights = analyze_schedule_insights(csv_data)
                    st.markdown(insights)
                
        else:
            st.error("Could not find a feasible schedule. Please check constraints (e.g., teacher availability, qualifications).")
