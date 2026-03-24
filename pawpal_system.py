"""
PawPal+ — core backend logic.

Classes
-------
Task          : a single pet-care activity (dataclass)
Pet           : a pet with a list of tasks (dataclass)
Owner         : the person who cares for the pets
ScheduledTask : a Task placed on the clock
Scheduler     : builds and validates a daily plan
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Constants ────────────────────────────────────────────────────────────────

class Priority(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

PRIORITY_WEIGHT = {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}

CATEGORY_DEFAULTS: dict[str, int] = {
    "walk":        30,
    "feeding":     10,
    "medication":   5,
    "grooming":    20,
    "appointment": 60,
    "enrichment":  15,
    "other":       15,
}


# ── Task ─────────────────────────────────────────────────────────────────────

@dataclass
class Task:
    """A single pet-care activity."""
    title: str
    category: str = "other"
    duration_minutes: int = 15
    priority: Priority = Priority.MEDIUM
    preferred_time: Optional[datetime.time] = None   # e.g. datetime.time(8, 0)
    is_recurring: bool = False
    recurrence_days: int = 1   # every N days (1 = daily)
    notes: str = ""
    completed: bool = False
    due_date: Optional[datetime.date] = None

    def __post_init__(self) -> None:
        # Normalise priority to enum
        if isinstance(self.priority, str):
            self.priority = Priority(self.priority.lower())
        # Auto-fill duration from category defaults when caller left it at 15
        if self.duration_minutes == 15 and self.category in CATEGORY_DEFAULTS:
            self.duration_minutes = CATEGORY_DEFAULTS[self.category]
        # Default due date to today
        if self.due_date is None:
            self.due_date = datetime.date.today()

    @property
    def priority_weight(self) -> int:
        """Return numeric weight for priority comparison (high=3, medium=2, low=1)."""
        return PRIORITY_WEIGHT[self.priority]

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as completed.

        For recurring tasks, also returns a new Task instance scheduled for
        the next occurrence (today + recurrence_days). For one-off tasks
        returns None.
        """
        self.completed = True
        if self.is_recurring:
            next_due = (self.due_date or datetime.date.today()) + datetime.timedelta(
                days=self.recurrence_days
            )
            return Task(
                title=self.title,
                category=self.category,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                preferred_time=self.preferred_time,
                is_recurring=self.is_recurring,
                recurrence_days=self.recurrence_days,
                notes=self.notes,
                completed=False,
                due_date=next_due,
            )
        return None

    def __str__(self) -> str:
        """Return a concise human-readable description of the task."""
        rec    = f" (every {self.recurrence_days}d)" if self.is_recurring else ""
        status = " ✓" if self.completed else ""
        return f"[{self.priority.value.upper()}] {self.title} ({self.duration_minutes} min){rec}{status}"


# ── Pet ───────────────────────────────────────────────────────────────────────

@dataclass
class Pet:
    """A pet owned by the Owner."""
    name: str
    species: str = "dog"
    breed: str = ""
    age_years: float = 0.0
    special_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove the first task whose title matches; return True if removed."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.title != title]
        return len(self.tasks) < before

    def get_tasks_by_priority(self) -> list[Task]:
        """Return tasks sorted highest-priority first."""
        return sorted(self.tasks, key=lambda t: t.priority_weight, reverse=True)

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that have not been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def mark_task_complete(self, title: str) -> bool:
        """Mark the named task complete and auto-schedule its next occurrence.

        For recurring tasks a new Task is appended for the next due date.
        Returns True if the task was found and marked.
        """
        for task in self.tasks:
            if task.title == title and not task.completed:
                next_task = task.mark_complete()
                if next_task is not None:
                    self.tasks.append(next_task)
                return True
        return False

    def __str__(self) -> str:
        breed = f" ({self.breed})" if self.breed else ""
        return f"{self.name}{breed} — {self.species}, {self.age_years}yr"


# ── Owner ─────────────────────────────────────────────────────────────────────

class Owner:
    """A person who owns one or more pets."""

    def __init__(
        self,
        name: str,
        available_minutes: int = 120,
        wake_time: datetime.time = datetime.time(7, 0),
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes   # total care budget for the day
        self.wake_time = wake_time
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        before = len(self.pets)
        self.pets = [p for p in self.pets if p.name != name]
        return len(self.pets) < before

    def all_tasks(self) -> list[Task]:
        """Return every task across all pets (flat list)."""
        return [task for pet in self.pets for task in pet.tasks]

    def __str__(self) -> str:
        pets = ", ".join(p.name for p in self.pets) or "none"
        return f"Owner: {self.name} | {self.available_minutes} min/day | Pets: {pets}"


# ── ScheduledTask ─────────────────────────────────────────────────────────────

@dataclass
class ScheduledTask:
    """A Task placed at a specific clock time."""
    task: Task
    pet_name: str
    start_time: datetime.time
    end_time: datetime.time
    reason: str = ""

    @property
    def duration_minutes(self) -> int:
        start = datetime.datetime.combine(datetime.date.today(), self.start_time)
        end   = datetime.datetime.combine(datetime.date.today(), self.end_time)
        return int((end - start).total_seconds() // 60)

    def overlaps(self, other: "ScheduledTask") -> bool:
        """True when the two time blocks overlap."""
        s1 = datetime.datetime.combine(datetime.date.today(), self.start_time)
        e1 = datetime.datetime.combine(datetime.date.today(), self.end_time)
        s2 = datetime.datetime.combine(datetime.date.today(), other.start_time)
        e2 = datetime.datetime.combine(datetime.date.today(), other.end_time)
        return s1 < e2 and s2 < e1

    def __str__(self) -> str:
        return (
            f"{self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}  "
            f"{self.task.title} [{self.pet_name}]  ({self.reason})"
        )


# ── Scheduler ─────────────────────────────────────────────────────────────────

class Scheduler:
    """
    Builds a daily care schedule for all of an Owner's pets.

    Algorithm
    ---------
    1. Collect every Task from every Pet.
    2. Sort by priority (high → low), then by preferred_time if set.
    3. Walk through the sorted list; assign each task a start time equal
       to current_cursor and advance the cursor.
    4. If a task has a preferred_time, insert it as close to that slot as
       possible (without moving already-scheduled tasks backward).
    5. Skip tasks that would push total minutes beyond the owner's budget.
    6. Detect and report any time conflicts that were forced in by preferred_time.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.schedule: list[ScheduledTask] = []
        self.skipped: list[tuple[Task, str, str]] = []  # (task, pet_name, reason)
        self.conflicts: list[tuple[ScheduledTask, ScheduledTask]] = []

    # ── Public API ───────────────────────────────────────────────────────────

    def generate_schedule(self) -> list[ScheduledTask]:
        """Build and return today's schedule."""
        self.schedule.clear()
        self.skipped.clear()
        self.conflicts.clear()

        tasks_with_pet = self._collect_tasks()
        tasks_with_pet = self._sort_tasks(tasks_with_pet)

        cursor = datetime.datetime.combine(datetime.date.today(), self.owner.wake_time)
        minutes_used = 0

        for task, pet_name in tasks_with_pet:
            if minutes_used + task.duration_minutes > self.owner.available_minutes:
                self.skipped.append((task, pet_name, "exceeds daily time budget"))
                continue

            # Use preferred_time when possible
            if task.preferred_time is not None:
                preferred_dt = datetime.datetime.combine(
                    datetime.date.today(), task.preferred_time
                )
                start = max(cursor, preferred_dt)
            else:
                start = cursor

            end = start + datetime.timedelta(minutes=task.duration_minutes)

            reason = self._build_reason(task, start, cursor)
            st = ScheduledTask(
                task=task,
                pet_name=pet_name,
                start_time=start.time(),
                end_time=end.time(),
                reason=reason,
            )
            self.schedule.append(st)
            minutes_used += task.duration_minutes
            cursor = end

        self._detect_conflicts()
        return self.schedule

    def detect_conflicts(self) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Return pairs of ScheduledTasks whose time blocks overlap."""
        self._detect_conflicts()
        return self.conflicts

    def sort_by_time(self) -> list[ScheduledTask]:
        """Return the current schedule sorted by start_time (earliest first)."""
        return sorted(self.schedule, key=lambda st: st.start_time)

    def filter_by_pet(self, pet_name: str) -> list[ScheduledTask]:
        """Return only scheduled tasks that belong to the named pet."""
        return [st for st in self.schedule if st.pet_name == pet_name]

    def filter_by_status(self, completed: bool) -> list[ScheduledTask]:
        """Return scheduled tasks whose underlying Task has the given completion status."""
        return [st for st in self.schedule if st.task.completed == completed]

    def summary(self) -> str:
        """Human-readable summary of the generated schedule."""
        if not self.schedule:
            return "No schedule generated yet. Call generate_schedule() first."

        lines: list[str] = []
        lines.append(f"=== Daily Care Plan for {self.owner.name} ===")
        lines.append(
            f"Start: {self.owner.wake_time.strftime('%H:%M')}  |  "
            f"Budget: {self.owner.available_minutes} min  |  "
            f"Tasks scheduled: {len(self.schedule)}"
        )
        lines.append("")

        for st in self.schedule:
            lines.append(str(st))

        if self.skipped:
            lines.append("")
            lines.append("--- Skipped (over budget) ---")
            for task, pet_name, reason in self.skipped:
                lines.append(f"  {task.title} [{pet_name}]: {reason}")

        if self.conflicts:
            lines.append("")
            lines.append("--- Conflicts detected ---")
            for a, b in self.conflicts:
                lines.append(f"  OVERLAP: '{a.task.title}' and '{b.task.title}'")

        total = sum(st.duration_minutes for st in self.schedule)
        lines.append("")
        lines.append(f"Total time used: {total} / {self.owner.available_minutes} min")
        return "\n".join(lines)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _collect_tasks(self) -> list[tuple[Task, str]]:
        result = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                result.append((task, pet.name))
        return result

    @staticmethod
    def _sort_tasks(
        tasks_with_pet: list[tuple[Task, str]]
    ) -> list[tuple[Task, str]]:
        """
        Primary sort: priority weight (high first).
        Secondary sort: preferred_time (earlier preferred slots first;
                        tasks with no preferred_time go last within
                        the same priority tier).
        """
        def sort_key(item: tuple[Task, str]) -> tuple[int, datetime.datetime]:
            task, _ = item
            if task.preferred_time is not None:
                pt = datetime.datetime.combine(datetime.date.today(), task.preferred_time)
            else:
                # Push no-preference tasks to end of priority tier
                pt = datetime.datetime.combine(
                    datetime.date.today(), datetime.time(23, 59)
                )
            return (-task.priority_weight, pt)

        return sorted(tasks_with_pet, key=sort_key)

    def _detect_conflicts(self) -> None:
        self.conflicts.clear()
        for i, a in enumerate(self.schedule):
            for b in self.schedule[i + 1:]:
                if a.overlaps(b):
                    self.conflicts.append((a, b))

    @staticmethod
    def _build_reason(
        task: Task,
        actual_start: datetime.datetime,
        cursor: datetime.datetime,
    ) -> str:
        parts = [f"priority={task.priority.value}"]
        if task.preferred_time is not None:
            pref = datetime.datetime.combine(
                datetime.date.today(), task.preferred_time
            )
            if actual_start > cursor:
                parts.append(f"delayed to preferred time {task.preferred_time.strftime('%H:%M')}")
            else:
                parts.append(
                    f"preferred {pref.strftime('%H:%M')}, "
                    f"started at cursor ({actual_start.strftime('%H:%M')})"
                )
        return ", ".join(parts)
