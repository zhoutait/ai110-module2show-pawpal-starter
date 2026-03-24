"""
main.py — CLI demo and manual test harness for PawPal+

Run:
    python main.py       (or: python3 main.py)

Exercises:
  * Creating owners and pets
  * Adding / sorting / filtering tasks
  * Generating a daily schedule
  * Recurring task auto-scheduling
  * Conflict detection
"""

import datetime
from pawpal_system import Owner, Pet, Task, Priority, Scheduler


def separator(title: str = "") -> None:
    """Print a visible section separator."""
    print()
    print("─" * 55)
    if title:
        print(f"  {title}")
        print("─" * 55)


def demo_basic_schedule() -> None:
    separator("Basic schedule — two pets, six tasks")

    # ── Owner ─────────────────────────────────────────────────
    jordan = Owner(
        name="Jordan",
        available_minutes=120,
        wake_time=datetime.time(7, 0),
    )

    # ── Pet 1 ─────────────────────────────────────────────────
    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age_years=3.0)
    mochi.add_task(Task(
        title="Breakfast feeding",
        category="feeding",
        priority=Priority.HIGH,
        preferred_time=datetime.time(7, 0),
    ))
    mochi.add_task(Task(
        title="Joint supplement",
        category="medication",
        duration_minutes=5,
        priority=Priority.HIGH,
        preferred_time=datetime.time(7, 10),
        notes="Give with food",
    ))
    mochi.add_task(Task(
        title="Morning walk",
        category="walk",
        priority=Priority.HIGH,
        preferred_time=datetime.time(7, 30),
    ))
    mochi.add_task(Task(
        title="Evening walk",
        category="walk",
        priority=Priority.MEDIUM,
        preferred_time=datetime.time(17, 0),
    ))
    mochi.add_task(Task(
        title="Puzzle toy",
        category="enrichment",
        priority=Priority.LOW,
        is_recurring=True,
        recurrence_days=2,
    ))
    jordan.add_pet(mochi)

    # ── Pet 2 ─────────────────────────────────────────────────
    luna = Pet(name="Luna", species="cat", age_years=2.0)
    luna.add_task(Task(
        title="Cat feeding",
        category="feeding",
        priority=Priority.HIGH,
        preferred_time=datetime.time(7, 15),
    ))
    luna.add_task(Task(
        title="Litter box",
        category="other",
        duration_minutes=5,
        priority=Priority.MEDIUM,
    ))
    jordan.add_pet(luna)

    # ── Generate schedule ─────────────────────────────────────
    scheduler = Scheduler(jordan)
    scheduler.generate_schedule()
    print(scheduler.summary())

    # ── Sort by time ──────────────────────────────────────────
    separator("Sorted by start time")
    for st in scheduler.sort_by_time():
        print(f"  {st}")

    # ── Filter by pet ─────────────────────────────────────────
    separator("Mochi's tasks only")
    for st in scheduler.filter_by_pet("Mochi"):
        print(f"  {st}")


def demo_recurring_tasks() -> None:
    separator("Recurring task — mark complete and auto-schedule next")

    pet = Pet(name="Rex", species="dog")
    pet.add_task(Task(
        title="Daily walk",
        category="walk",
        priority=Priority.HIGH,
        is_recurring=True,
        recurrence_days=1,
    ))

    print(f"  Tasks before: {[str(t) for t in pet.tasks]}")
    pet.mark_task_complete("Daily walk")
    print(f"  Tasks after:  {[str(t) for t in pet.tasks]}")

    # The completed task should remain, and a new pending one should exist
    completed = [t for t in pet.tasks if t.completed]
    pending   = [t for t in pet.tasks if not t.completed]
    print(f"  Completed: {len(completed)}  |  Pending (next occurrence): {len(pending)}")
    if pending:
        print(f"  Next due date: {pending[0].due_date}")


def demo_conflict_detection() -> None:
    separator("Conflict detection — two tasks forced into same slot")

    owner = Owner("Alex", available_minutes=120, wake_time=datetime.time(9, 0))
    pet   = Pet("Buddy", species="dog")

    # Both prefer 09:00 — the second one will be forced to start right after
    # the first, which means no true conflict in sequential mode.
    # To force a real conflict we would need two tasks to be placed there
    # simultaneously; the sequential cursor prevents that in normal operation.
    # Demonstrate with back-to-back preferred times that DO overlap:
    pet.add_task(Task(
        title="Task A",
        duration_minutes=30,
        priority=Priority.HIGH,
        preferred_time=datetime.time(9, 0),
    ))
    pet.add_task(Task(
        title="Task B",
        duration_minutes=30,
        priority=Priority.HIGH,
        preferred_time=datetime.time(9, 10),  # 10 min in — overlaps Task A
    ))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()

    if scheduler.conflicts:
        print(f"  ⚠️  {len(scheduler.conflicts)} conflict(s) detected:")
        for a, b in scheduler.conflicts:
            print(f"     '{a.task.title}' ({a.start_time}–{a.end_time}) "
                  f"overlaps '{b.task.title}' ({b.start_time}–{b.end_time})")
    else:
        print("  No conflicts — scheduler resolved preferred-time collision sequentially.")
    print(scheduler.summary())


def demo_today_schedule() -> None:
    separator("Today's schedule — printed in readable format")
    owner = Owner("Sam", available_minutes=60, wake_time=datetime.time(8, 0))
    pet   = Pet("Pepper", species="dog")
    pet.add_task(Task("Feeding",  category="feeding",    priority=Priority.HIGH))
    pet.add_task(Task("Walk",     category="walk",       priority=Priority.HIGH))
    pet.add_task(Task("Grooming", category="grooming",   priority=Priority.LOW))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    schedule  = scheduler.generate_schedule()

    print(f"\n  Today's Care Plan for {owner.name}")
    print(f"  {'─'*45}")
    for item in schedule:
        status = "✓" if item.task.completed else "○"
        print(
            f"  {status}  {item.start_time.strftime('%H:%M')}  "
            f"{item.task.title:<20} [{item.pet_name}]  ({item.task.priority.value})"
        )
    if scheduler.skipped:
        print(f"\n  Skipped ({len(scheduler.skipped)}):")
        for t, pet_name, reason in scheduler.skipped:
            print(f"     • {t.title} [{pet_name}]: {reason}")


if __name__ == "__main__":
    print("=" * 55)
    print("  PawPal+ — CLI Demo (main.py)")
    print("=" * 55)

    demo_basic_schedule()
    demo_recurring_tasks()
    demo_conflict_detection()
    demo_today_schedule()

    print()
    print("=" * 55)
    print("  All demos complete.")
    print("=" * 55)
