"""
test_pawpal.py — pytest suite for PawPal+ backend

Run:
    pytest test_pawpal.py -v
"""

import datetime
import pytest
from pawpal_system import (
    Owner, Pet, Task, Priority, Scheduler, ScheduledTask,
    PRIORITY_WEIGHT,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def simple_owner() -> Owner:
    return Owner(
        name="Test Owner",
        available_minutes=60,
        wake_time=datetime.time(8, 0),
    )


@pytest.fixture
def simple_pet() -> Pet:
    pet = Pet(name="Buddy", species="dog")
    pet.add_task(Task("Walk", category="walk", priority=Priority.HIGH))
    pet.add_task(Task("Feed", category="feeding", priority=Priority.MEDIUM))
    pet.add_task(Task("Play", category="enrichment", priority=Priority.LOW))
    return pet


# ── Task tests ────────────────────────────────────────────────────────────────

class TestTask:
    def test_priority_enum_from_string(self):
        t = Task("x", priority="high")
        assert t.priority == Priority.HIGH

    def test_priority_weight(self):
        assert Task("x", priority=Priority.HIGH).priority_weight == 3
        assert Task("x", priority=Priority.MEDIUM).priority_weight == 2
        assert Task("x", priority=Priority.LOW).priority_weight == 1

    def test_category_autofills_duration(self):
        t = Task("Walk", category="walk")
        assert t.duration_minutes == 30

    def test_duration_override_not_replaced(self):
        # If caller explicitly sets a non-default duration, honour it
        t = Task("Long walk", category="walk", duration_minutes=60)
        assert t.duration_minutes == 60

    def test_str_includes_priority_and_title(self):
        t = Task("Morning walk", priority=Priority.HIGH)
        assert "HIGH" in str(t)
        assert "Morning walk" in str(t)


# ── Pet tests ─────────────────────────────────────────────────────────────────

class TestPet:
    def test_add_task(self, simple_pet):
        before = len(simple_pet.tasks)
        simple_pet.add_task(Task("New task"))
        assert len(simple_pet.tasks) == before + 1

    def test_remove_task_by_title(self, simple_pet):
        removed = simple_pet.remove_task("Walk")
        assert removed is True
        assert all(t.title != "Walk" for t in simple_pet.tasks)

    def test_remove_nonexistent_task_returns_false(self, simple_pet):
        assert simple_pet.remove_task("Does not exist") is False

    def test_get_tasks_by_priority_order(self, simple_pet):
        sorted_tasks = simple_pet.get_tasks_by_priority()
        weights = [t.priority_weight for t in sorted_tasks]
        assert weights == sorted(weights, reverse=True)


# ── Owner tests ───────────────────────────────────────────────────────────────

class TestOwner:
    def test_add_pet(self, simple_owner, simple_pet):
        simple_owner.add_pet(simple_pet)
        assert simple_pet in simple_owner.pets

    def test_remove_pet(self, simple_owner, simple_pet):
        simple_owner.add_pet(simple_pet)
        removed = simple_owner.remove_pet("Buddy")
        assert removed is True
        assert all(p.name != "Buddy" for p in simple_owner.pets)

    def test_all_tasks_flattens_across_pets(self, simple_owner):
        pet1 = Pet("A")
        pet1.add_task(Task("T1"))
        pet2 = Pet("B")
        pet2.add_task(Task("T2"))
        pet2.add_task(Task("T3"))
        simple_owner.add_pet(pet1)
        simple_owner.add_pet(pet2)
        assert len(simple_owner.all_tasks()) == 3


# ── Scheduler tests ───────────────────────────────────────────────────────────

class TestScheduler:
    def _make_scheduler(
        self,
        available_minutes: int = 120,
        wake_time: datetime.time = datetime.time(8, 0),
    ) -> Scheduler:
        owner = Owner("J", available_minutes=available_minutes, wake_time=wake_time)
        return Scheduler(owner)

    def test_empty_schedule_for_owner_with_no_pets(self):
        s = self._make_scheduler()
        result = s.generate_schedule()
        assert result == []

    def test_tasks_scheduled_in_priority_order(self):
        owner = Owner("J", available_minutes=120, wake_time=datetime.time(8, 0))
        pet = Pet("P")
        pet.add_task(Task("Low task",  priority=Priority.LOW,    duration_minutes=10))
        pet.add_task(Task("High task", priority=Priority.HIGH,   duration_minutes=10))
        pet.add_task(Task("Med task",  priority=Priority.MEDIUM, duration_minutes=10))
        owner.add_pet(pet)

        result = Scheduler(owner).generate_schedule()
        titles = [st.task.title for st in result]
        assert titles.index("High task") < titles.index("Med task")
        assert titles.index("Med task") < titles.index("Low task")

    def test_tasks_that_exceed_budget_are_skipped(self):
        owner = Owner("J", available_minutes=10, wake_time=datetime.time(8, 0))
        pet = Pet("P")
        pet.add_task(Task("Short", duration_minutes=5,  priority=Priority.HIGH))
        pet.add_task(Task("Long",  duration_minutes=30, priority=Priority.MEDIUM))
        owner.add_pet(pet)

        s = Scheduler(owner)
        s.generate_schedule()

        scheduled_titles = [st.task.title for st in s.schedule]
        skipped_titles   = [t.title for t, _, _ in s.skipped]

        assert "Short" in scheduled_titles
        assert "Long"  in skipped_titles

    def test_preferred_time_is_respected(self):
        owner = Owner("J", available_minutes=60, wake_time=datetime.time(7, 0))
        pet = Pet("P")
        pet.add_task(Task(
            "Meds",
            category="medication",
            priority=Priority.HIGH,
            preferred_time=datetime.time(9, 0),
        ))
        owner.add_pet(pet)

        result = Scheduler(owner).generate_schedule()
        assert len(result) == 1
        # Should start at or after 09:00
        assert result[0].start_time >= datetime.time(9, 0)

    def test_no_time_travel_start_after_wake(self):
        owner = Owner("J", available_minutes=60, wake_time=datetime.time(8, 0))
        pet = Pet("P")
        # Preferred time BEFORE wake time — cursor should dominate
        pet.add_task(Task(
            "Early",
            duration_minutes=10,
            priority=Priority.HIGH,
            preferred_time=datetime.time(6, 0),  # 06:00 < 08:00 wake
        ))
        owner.add_pet(pet)

        result = Scheduler(owner).generate_schedule()
        assert result[0].start_time >= datetime.time(8, 0)

    def test_consecutive_tasks_do_not_overlap(self):
        owner = Owner("J", available_minutes=60, wake_time=datetime.time(8, 0))
        pet = Pet("P")
        for i in range(3):
            pet.add_task(Task(f"Task{i}", duration_minutes=10, priority=Priority.MEDIUM))
        owner.add_pet(pet)

        s = Scheduler(owner)
        s.generate_schedule()
        assert s.conflicts == []

    def test_scheduled_task_duration_is_correct(self):
        owner = Owner("J", available_minutes=60, wake_time=datetime.time(8, 0))
        pet = Pet("P")
        pet.add_task(Task("Walk", duration_minutes=30, priority=Priority.HIGH))
        owner.add_pet(pet)

        result = Scheduler(owner).generate_schedule()
        assert result[0].duration_minutes == 30

    def test_summary_contains_owner_name(self):
        owner = Owner("Jordan", available_minutes=30, wake_time=datetime.time(7, 0))
        pet = Pet("P")
        pet.add_task(Task("Feed", duration_minutes=10))
        owner.add_pet(pet)

        s = Scheduler(owner)
        s.generate_schedule()
        assert "Jordan" in s.summary()

    def test_zero_available_minutes_skips_everything(self):
        owner = Owner("J", available_minutes=0, wake_time=datetime.time(8, 0))
        pet = Pet("P")
        pet.add_task(Task("Task", duration_minutes=5))
        owner.add_pet(pet)

        s = Scheduler(owner)
        s.generate_schedule()
        assert s.schedule == []
        assert len(s.skipped) == 1


# ── ScheduledTask overlap test ────────────────────────────────────────────────

class TestScheduledTaskOverlap:
    def _make_st(self, h_start: int, h_end: int) -> ScheduledTask:
        t = Task("x")
        return ScheduledTask(
            task=t,
            pet_name="P",
            start_time=datetime.time(h_start, 0),
            end_time=datetime.time(h_end, 0),
        )

    def test_non_overlapping_returns_false(self):
        a = self._make_st(8, 9)
        b = self._make_st(9, 10)
        assert not a.overlaps(b)

    def test_overlapping_returns_true(self):
        a = self._make_st(8, 10)
        b = self._make_st(9, 11)
        assert a.overlaps(b)

    def test_contained_returns_true(self):
        a = self._make_st(8, 12)
        b = self._make_st(9, 11)
        assert a.overlaps(b)
