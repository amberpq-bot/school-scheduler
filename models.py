from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

@dataclass
class Teacher:
    id: str
    name: str
    qualifications: List[str]

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        return Teacher(
            id=d['id'],
            name=d['name'],
            qualifications=d.get('qualifications', [])
        )

@dataclass
class Room:
    id: str
    name: str
    capacity: int

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        return Room(
            id=d['id'],
            name=d['name'],
            capacity=int(d['capacity'])
        )

@dataclass
class SchoolClass:
    id: str
    name: str
    subject: str
    required_sessions: int = 1
    teacher_id: Optional[str] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        return SchoolClass(
            id=d['id'],
            name=d['name'],
            subject=d['subject'],
            required_sessions=int(d.get('required_sessions', 1)),
            teacher_id=d.get('teacher_id')
        )

@dataclass
class TimeSlot:
    id: str
    day: str
    period: int

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        return TimeSlot(
            id=d['id'],
            day=d['day'],
            period=int(d['period'])
        )

@dataclass
class ScheduledClass:
    class_id: str
    teacher_id: str
    room_id: str
    time_slot_id: str

@dataclass
class ScheduleResponse:
    status: str
    schedule: List[ScheduledClass]

    def to_dict(self):
        return {
            "status": self.status,
            "schedule": [asdict(s) for s in self.schedule]
        }
