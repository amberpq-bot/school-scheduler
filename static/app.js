// State
let teachers = [];
let rooms = [];
let classes = [];

// DOM Elements
const teacherList = document.getElementById('teacher-list');
const roomList = document.getElementById('room-list');
const classList = document.getElementById('class-list');
const classTeacherSelect = document.getElementById('class-teacher');

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

  document.getElementById(`${tabId}-tab`).classList.add('active');
  document.querySelector(`button[onclick="switchTab('${tabId}')"]`).classList.add('active');
}

// Helper: Generate ID
const uid = () => Date.now().toString(36) + Math.random().toString(36).substr(2);

// Teachers
function addTeacher() {
  const name = document.getElementById('teacher-name').value;
  const subjectsStr = document.getElementById('teacher-subjects').value;

  if (!name || !subjectsStr) return alert('Please fill in all fields');

  const teacher = {
    id: uid(),
    name,
    qualifications: subjectsStr.split(',').map(s => s.trim())
  };

  teachers.push(teacher);
  renderTeachers();
  updateTeacherSelect();

  document.getElementById('teacher-name').value = '';
  document.getElementById('teacher-subjects').value = '';
}

function renderTeachers() {
  teacherList.innerHTML = teachers.map(t => `
        <li>
            <span><strong>${t.name}</strong> (${t.qualifications.join(', ')})</span>
            <button class="delete-btn" onclick="removeTeacher('${t.id}')">Delete</button>
        </li>
    `).join('');
}

function removeTeacher(id) {
  teachers = teachers.filter(t => t.id !== id);
  renderTeachers();
  updateTeacherSelect();
}

function updateTeacherSelect() {
  classTeacherSelect.innerHTML = '<option value="">Any Qualified Teacher</option>' +
    teachers.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
}

// Rooms
function addRoom() {
  const name = document.getElementById('room-name').value;
  const capacity = parseInt(document.getElementById('room-capacity').value);

  if (!name) return alert('Please enter room name');

  const room = {
    id: uid(),
    name,
    capacity
  };

  rooms.push(room);
  renderRooms();

  document.getElementById('room-name').value = '';
}

function renderRooms() {
  roomList.innerHTML = rooms.map(r => `
        <li>
            <span><strong>${r.name}</strong> (Cap: ${r.capacity})</span>
            <button class="delete-btn" onclick="removeRoom('${r.id}')">Delete</button>
        </li>
    `).join('');
}

function removeRoom(id) {
  rooms = rooms.filter(r => r.id !== id);
  renderRooms();
}

// Classes
function addClass() {
  const name = document.getElementById('class-name').value;
  const subject = document.getElementById('class-subject').value;
  const sessions = parseInt(document.getElementById('class-sessions').value);
  const teacherId = document.getElementById('class-teacher').value || null;

  if (!name || !subject) return alert('Please fill in required fields');

  const newClass = {
    id: uid(),
    name,
    subject,
    required_sessions: sessions,
    teacher_id: teacherId
  };

  classes.push(newClass);
  renderClasses();

  document.getElementById('class-name').value = '';
  document.getElementById('class-subject').value = '';
}

function renderClasses() {
  classList.innerHTML = classes.map(c => {
    const tName = c.teacher_id ? teachers.find(t => t.id === c.teacher_id)?.name : 'Any';
    return `
            <li>
                <span><strong>${c.name}</strong> (${c.subject}) - ${c.required_sessions}x/week (Teacher: ${tName})</span>
                <button class="delete-btn" onclick="removeClass('${c.id}')">Delete</button>
            </li>
        `;
  }).join('');
}

function removeClass(id) {
  classes = classes.filter(c => c.id !== id);
  renderClasses();
}

// Schedule Generation
async function generateSchedule() {
  if (teachers.length === 0 || rooms.length === 0 || classes.length === 0) {
    return alert('Please add teachers, rooms, and classes first.');
  }

  document.getElementById('status-display').textContent = 'Generating...';

  // Create standard time slots (Mon-Fri, 5 slots per day for simplicity)
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
  const time_slots = [];
  let slotId = 0;
  days.forEach(day => {
    for (let period = 1; period <= 5; period++) {
      time_slots.push({
        id: `slot_${slotId++}`,
        day,
        period
      });
    }
  });

  const payload = {
    teachers,
    rooms,
    classes,
    time_slots
  };

  try {
    const response = await fetch('/api/solve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('Solver failed');

    const data = await response.json();
    document.getElementById('status-display').textContent = `Status: ${data.status}`;

    renderSchedule(data.schedule, time_slots);

  } catch (e) {
    console.error(e);
    document.getElementById('status-display').textContent = 'Error calling solver';
  }
}

function renderSchedule(schedule, timeSlots) {
  const grid = document.getElementById('schedule-grid');
  grid.innerHTML = '';

  // Headers
  grid.appendChild(createCell('Period', 'grid-header'));
  ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].forEach(d => grid.appendChild(createCell(d, 'grid-header')));

  // Rows
  for (let period = 1; period <= 5; period++) {
    // Period Label
    grid.appendChild(createCell(`Period ${period}`, 'grid-header'));

    // Days
    ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].forEach(day => {
      const cell = createCell('', 'grid-cell');

      // Find items in this slot
      const slot = timeSlots.find(s => s.day === day && s.period === period);
      if (slot) {
        const items = schedule.filter(item => item.time_slot_id === slot.id);
        items.forEach(item => {
          const cls = classes.find(c => c.id === item.class_id);
          const room = rooms.find(r => r.id === item.room_id);
          const teacher = teachers.find(t => t.id === item.teacher_id);

          const card = document.createElement('div');
          card.className = 'schedule-card';
          card.innerHTML = `
                        <strong>${cls ? cls.name : 'Unknown'}</strong><br>
                        ${room ? room.name : '?'}<br>
                        ${teacher ? teacher.name : '?'}
                    `;
          cell.appendChild(card);
        });
      }
      grid.appendChild(cell);
    });
  }
}

function createCell(text, className) {
  const div = document.createElement('div');
  div.className = className;
  div.textContent = text;
  return div;
}
