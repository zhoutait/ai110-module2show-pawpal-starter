"""
demo.py — CLI demo for PawPal+

Run:
    python demo.py

This script exercises every major feature of the backend before the
Streamlit UI is involved. Useful for quick sanity-checks.
"""

import datetime
from pawpal_system import Owner, Pet, Task, Priority, Scheduler


def main() -> None:
    print("=" * 55)
    print("  PawPal+ CLI Demo")
    print("=" * 55)

    # ── Build owner ───────────────────────────────────────────
    jordan = Owner(
        name="Jordan",
        available_minutes=90,
        wake_time=datetime.time(7, 0),
    )

    # ── Build pet ─────────────────────────────────────────────
    mochi = Pet(
        name="Mochi",
        species="dog",
        breed="Shiba Inu",
        age_years=3.0,
        special_needs=["joint supplement"],
    )

    # ── Add tasks ─────────────────────────────────────────────
    mochi.add_task(Task(
        title="Morning walk",
        category="walk",
        priority=Priority.HIGH,
        preferred_time=datetime.time(7, 30),
    ))
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
        preferred_time=datetime.time(7, 5),
        notes="Give with food",
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
    mochi.add_task(Task(
        title="Brushing",
        category="grooming",
        priority=Priority.LOW,
    ))

    jordan.add_pet(mochi)

    # ── Second pet ────────────────────────────────────────────
    luna = Pet(name="Luna", species="cat", age_years=2.0)
    luna.add_task(Task(
        title="Cat feeding",
        category="feeding",
        priority=Priority.HIGH,
        preferred_time=datetime.time(7, 10),
    ))
    luna.add_task(Task(
        title="Litter box",
        category="other",
        duration_minutes=5,
        priority=Priority.MEDIUM,
    ))
    jordan.add_pet(luna)

    print(jordan)
    print()

    # ── Print tasks by priority ───────────────────────────────
    print("--- Mochi's tasks (priority order) ---")
    for t in mochi.get_tasks_by_priority():
        print(" ", t)

    print()

    # ── Generate schedule ─────────────────────────────────────
    scheduler = Scheduler(jordan)
    scheduler.generate_schedule()
    print(scheduler.summary())

    # ── Demo: task over budget ────────────────────────────────
    print()
    print("--- Adding a 60-min appointment (may exceed budget) ---")
    mochi.add_task(Task(
        title="Vet appointment",
        category="appointment",
        priority=Priority.HIGH,
    ))
    scheduler2 = Scheduler(jordan)
    scheduler2.generate_schedule()
    print(scheduler2.summary())

    # ── Demo: conflict detection ──────────────────────────────
    print()
    print("--- Conflict detection demo ---")
    if scheduler2.conflicts:
        print(f"  {len(scheduler2.conflicts)} conflict(s) found:")
        for a, b in scheduler2.conflicts:
            print(f"    '{a.task.title}' overlaps '{b.task.title}'")
    else:
        print("  No conflicts detected.")


if __name__ == "__main__":
    main()
