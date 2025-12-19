from ortools.sat.python import cp_model
from typing import List, Dict, Tuple
from models import Teacher, Room, SchoolClass, TimeSlot, ScheduleResponse, ScheduledClass

class SchoolScheduler:
    def __init__(self, teachers: List[Teacher], rooms: List[Room], classes: List[SchoolClass], time_slots: List[TimeSlot]):
        self.teachers = teachers
        self.rooms = rooms
        self.classes = classes
        self.time_slots = time_slots
        
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Variables
        self.assignment_vars = {} # (c.id, t.id, r.id, s.id) -> BoolVar

    def solve(self) -> ScheduleResponse:
        # 1. Create Variables
        # x_c_t_r_s = 1 if class c is assign to teacher t in room r at slot s
        for c in self.classes:
            for t in self.teachers:
                # Qualification check
                if c.subject not in t.qualifications:
                    continue
                
                # Teacher Pre-assignment check
                if c.teacher_id and c.teacher_id != t.id:
                    continue

                for r in self.rooms:
                    for s in self.time_slots:
                        var_name = f'c{c.id}_t{t.id}_r{r.id}_s{s.id}'
                        self.assignment_vars[(c.id, t.id, r.id, s.id)] = self.model.NewBoolVar(var_name)

        # 2. Constraints

        # C1: Each class must be assigned exactly 'required_sessions' times
        for c in self.classes:
            c_vars = []
            for t in self.teachers:
                for r in self.rooms:
                    for s in self.time_slots:
                        if (c.id, t.id, r.id, s.id) in self.assignment_vars:
                            c_vars.append(self.assignment_vars[(c.id, t.id, r.id, s.id)])
            
            if c_vars:
                self.model.Add(sum(c_vars) == c.required_sessions)
            else:
                # Impossible to schedule this class (e.g. no qualified teacher)
                # We can't return early if we want to debug, but for now strict:
                pass 
                # If no variables exist for a class, it means NO qualified teacher found.
                # The constraint sum(c_vars) == required (where required > 0) will be 0 == N => False (INFEASIBLE).
                # So we can just Add(0 == 1) if c_vars is empty but required > 0
                if c.required_sessions > 0:
                     self.model.Add(0 == 1)

        # C2: Teacher Enforce Single Assignment per Slot
        for t in self.teachers:
            for s in self.time_slots:
                t_s_vars = []
                for c in self.classes:
                    for r in self.rooms:
                        if (c.id, t.id, r.id, s.id) in self.assignment_vars:
                            t_s_vars.append(self.assignment_vars[(c.id, t.id, r.id, s.id)])
                if t_s_vars:
                    self.model.Add(sum(t_s_vars) <= 1)

        # C3: Room Enforce Single Assignment per Slot
        for r in self.rooms:
            for s in self.time_slots:
                r_s_vars = []
                for c in self.classes:
                    for t in self.teachers:
                        if (c.id, t.id, r.id, s.id) in self.assignment_vars:
                            r_s_vars.append(self.assignment_vars[(c.id, t.id, r.id, s.id)])
                if r_s_vars:
                    self.model.Add(sum(r_s_vars) <= 1)

        # C4: Class Single Assignment per Slot (No concurrency for same class)
        for c in self.classes:
            for s in self.time_slots:
                c_s_vars = []
                for t in self.teachers:
                    for r in self.rooms:
                        if (c.id, t.id, r.id, s.id) in self.assignment_vars:
                            c_s_vars.append(self.assignment_vars[(c.id, t.id, r.id, s.id)])
                if c_s_vars:
                    self.model.Add(sum(c_s_vars) <= 1)

        # 3. Solve
        status = self.solver.Solve(self.model)
        
        # 4. Extract Solution
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            schedule = []
            for (c_id, t_id, r_id, s_id), var in self.assignment_vars.items():
                if self.solver.Value(var) == 1:
                    schedule.append(ScheduledClass(
                        class_id=c_id,
                        teacher_id=t_id,
                        room_id=r_id,
                        time_slot_id=s_id
                    ))
            
            status_str = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
            return ScheduleResponse(status=status_str, schedule=schedule)
        
        return ScheduleResponse(status="INFEASIBLE", schedule=[])