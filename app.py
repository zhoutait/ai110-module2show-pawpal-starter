"""
app.py — PawPal+ Streamlit UI

Run:
    streamlit run app.py
"""

import datetime
import streamlit as st

from pawpal_system import Owner, Pet, Task, Priority, Scheduler


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — powered by Python OOP")

# ── Session-state defaults ────────────────────────────────────────────────────

def _init_state() -> None:
    if "owner_name" not in st.session_state:
        st.session_state.owner_name = "Jordan"
    if "available_minutes" not in st.session_state:
        st.session_state.available_minutes = 120
    if "wake_hour" not in st.session_state:
        st.session_state.wake_hour = 7
    if "wake_minute" not in st.session_state:
        st.session_state.wake_minute = 0
    if "pets" not in st.session_state:
        # list of dicts: {name, species, breed, age, special_needs}
        st.session_state.pets = []
    if "tasks" not in st.session_state:
        # list of dicts: {pet_name, title, category, duration, priority,
        #                  has_preferred, pref_hour, pref_minute,
        #                  is_recurring, recurrence_days, notes}
        st.session_state.tasks = []

_init_state()


# ── Sidebar — Owner + Pet setup ───────────────────────────────────────────────

with st.sidebar:
    st.header("Owner & Pets")

    st.subheader("Owner info")
    st.session_state.owner_name = st.text_input(
        "Your name", value=st.session_state.owner_name
    )
    st.session_state.available_minutes = st.number_input(
        "Time available today (minutes)",
        min_value=5, max_value=480,
        value=st.session_state.available_minutes,
        step=5,
    )
    col_h, col_m = st.columns(2)
    with col_h:
        st.session_state.wake_hour = st.number_input(
            "Wake hour", min_value=0, max_value=23,
            value=st.session_state.wake_hour,
        )
    with col_m:
        st.session_state.wake_minute = st.number_input(
            "Wake minute", min_value=0, max_value=59,
            value=st.session_state.wake_minute,
            step=5,
        )

    st.divider()

    st.subheader("Add a pet")
    with st.form("add_pet_form", clear_on_submit=True):
        p_name    = st.text_input("Pet name", value="Mochi")
        p_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        p_breed   = st.text_input("Breed (optional)", value="")
        p_age     = st.number_input("Age (years)", min_value=0.0, max_value=30.0,
                                    value=1.0, step=0.5)
        p_needs   = st.text_input("Special needs (comma-separated)", value="")
        if st.form_submit_button("Add pet"):
            if p_name.strip():
                # Prevent duplicate pet names
                existing = [p["name"] for p in st.session_state.pets]
                if p_name.strip() in existing:
                    st.warning(f"A pet named '{p_name.strip()}' already exists.")
                else:
                    st.session_state.pets.append({
                        "name": p_name.strip(),
                        "species": p_species,
                        "breed": p_breed.strip(),
                        "age": p_age,
                        "special_needs": [
                            n.strip() for n in p_needs.split(",") if n.strip()
                        ],
                    })
                    st.success(f"Added {p_name.strip()}!")

    if st.session_state.pets:
        st.subheader("Your pets")
        for i, p in enumerate(st.session_state.pets):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                needs = ", ".join(p["special_needs"]) if p["special_needs"] else "—"
                st.write(f"**{p['name']}** ({p['species']}, {p['age']}yr) • {needs}")
            with col_b:
                if st.button("Remove", key=f"rem_pet_{i}"):
                    # Also remove tasks for that pet
                    st.session_state.tasks = [
                        t for t in st.session_state.tasks
                        if t["pet_name"] != p["name"]
                    ]
                    st.session_state.pets.pop(i)
                    st.rerun()


# ── Main area ─────────────────────────────────────────────────────────────────

tab_tasks, tab_schedule = st.tabs(["Tasks", "Schedule"])

# ── Tab 1: Tasks ──────────────────────────────────────────────────────────────

with tab_tasks:
    st.subheader("Add a care task")

    if not st.session_state.pets:
        st.info("Add at least one pet in the sidebar before adding tasks.")
    else:
        pet_names = [p["name"] for p in st.session_state.pets]

        with st.form("add_task_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_pet      = st.selectbox("For which pet?", pet_names)
                t_title    = st.text_input("Task title", value="Morning walk")
                t_category = st.selectbox(
                    "Category",
                    ["walk", "feeding", "medication", "grooming",
                     "appointment", "enrichment", "other"],
                )
            with col2:
                t_priority = st.selectbox("Priority", ["high", "medium", "low"], index=0)
                t_duration = st.number_input(
                    "Duration (minutes)", min_value=1, max_value=240, value=20, step=5
                )
                t_notes    = st.text_input("Notes (optional)", value="")

            st.markdown("**Preferred time (optional)**")
            col3, col4, col5 = st.columns(3)
            with col3:
                has_pref = st.checkbox("Set preferred time")
            with col4:
                pref_h = st.number_input("Hour",   min_value=0, max_value=23, value=8,  disabled=not has_pref)
            with col5:
                pref_m = st.number_input("Minute", min_value=0, max_value=59, value=0,
                                         step=15, disabled=not has_pref)

            col6, col7 = st.columns(2)
            with col6:
                is_rec = st.checkbox("Recurring task")
            with col7:
                rec_days = st.number_input(
                    "Every N days", min_value=1, max_value=30, value=1, disabled=not is_rec
                )

            if st.form_submit_button("Add task"):
                if t_title.strip():
                    st.session_state.tasks.append({
                        "pet_name":       t_pet,
                        "title":          t_title.strip(),
                        "category":       t_category,
                        "duration":       int(t_duration),
                        "priority":       t_priority,
                        "has_preferred":  has_pref,
                        "pref_hour":      int(pref_h),
                        "pref_minute":    int(pref_m),
                        "is_recurring":   is_rec,
                        "recurrence_days": int(rec_days),
                        "notes":          t_notes.strip(),
                    })
                    st.success(f"Task '{t_title.strip()}' added for {t_pet}!")

        # Task table
        if st.session_state.tasks:
            st.subheader("Current tasks")
            for i, t in enumerate(st.session_state.tasks):
                pref = (
                    f"{t['pref_hour']:02d}:{t['pref_minute']:02d}"
                    if t["has_preferred"] else "—"
                )
                rec = f"every {t['recurrence_days']}d" if t["is_recurring"] else "one-off"
                col_a, col_b = st.columns([5, 1])
                with col_a:
                    st.write(
                        f"**[{t['priority'].upper()}]** {t['title']} "
                        f"({t['pet_name']}) — {t['category']}, "
                        f"{t['duration']} min, pref={pref}, {rec}"
                    )
                with col_b:
                    if st.button("Remove", key=f"rem_task_{i}"):
                        st.session_state.tasks.pop(i)
                        st.rerun()
        else:
            st.info("No tasks yet. Add one above.")


# ── Tab 2: Schedule ───────────────────────────────────────────────────────────

with tab_schedule:
    st.subheader("Generate today's schedule")

    if not st.session_state.pets:
        st.info("Add pets and tasks first.")
    elif not st.session_state.tasks:
        st.info("Add at least one task in the Tasks tab.")
    else:
        if st.button("Generate schedule", type="primary"):
            # Build domain objects
            wake = datetime.time(
                st.session_state.wake_hour,
                st.session_state.wake_minute,
            )
            owner = Owner(
                name=st.session_state.owner_name,
                available_minutes=st.session_state.available_minutes,
                wake_time=wake,
            )

            pet_map: dict[str, Pet] = {}
            for p_data in st.session_state.pets:
                pet = Pet(
                    name=p_data["name"],
                    species=p_data["species"],
                    breed=p_data["breed"],
                    age_years=p_data["age"],
                    special_needs=p_data["special_needs"],
                )
                pet_map[p_data["name"]] = pet
                owner.add_pet(pet)

            for t_data in st.session_state.tasks:
                if t_data["pet_name"] not in pet_map:
                    continue
                preferred = (
                    datetime.time(t_data["pref_hour"], t_data["pref_minute"])
                    if t_data["has_preferred"] else None
                )
                task = Task(
                    title=t_data["title"],
                    category=t_data["category"],
                    duration_minutes=t_data["duration"],
                    priority=Priority(t_data["priority"]),
                    preferred_time=preferred,
                    is_recurring=t_data["is_recurring"],
                    recurrence_days=t_data["recurrence_days"],
                    notes=t_data["notes"],
                )
                pet_map[t_data["pet_name"]].add_task(task)

            scheduler = Scheduler(owner)
            schedule  = scheduler.generate_schedule()

            # ── Results ──────────────────────────────────────────────
            total_used = sum(item.task.duration_minutes for item in schedule)

            st.success(
                f"Schedule generated: **{len(schedule)} task(s)** | "
                f"**{total_used}/{owner.available_minutes} min** used"
            )

            if scheduler.conflicts:
                st.error(
                    f"⚠️ {len(scheduler.conflicts)} time conflict(s) detected — "
                    "review the warnings below."
                )
                for a, b in scheduler.conflicts:
                    st.warning(f"**Conflict:** '{a.task.title}' ({a.start_time.strftime('%H:%M')}–{a.end_time.strftime('%H:%M')}) overlaps with '{b.task.title}' ({b.start_time.strftime('%H:%M')}–{b.end_time.strftime('%H:%M')})")

            st.divider()
            st.subheader("Schedule View Options")
            col_sort, col_filter = st.columns(2)
            with col_sort:
                sort_time = st.checkbox("Sort chronologically", value=True)
            with col_filter:
                filter_pet = st.selectbox("Filter by pet", ["All"] + list(pet_map.keys()))

            display_schedule = schedule
            if sort_time:
                display_schedule = scheduler.sort_by_time()
            
            if filter_pet != "All":
                display_schedule = [item for item in display_schedule if item.pet_name == filter_pet]

            # Timeline table
            rows = []
            for st_item in display_schedule:
                rows.append({
                    "Time":     f"{st_item.start_time.strftime('%H:%M')} – {st_item.end_time.strftime('%H:%M')}",
                    "Pet":      st_item.pet_name,
                    "Task":     st_item.task.title,
                    "Category": st_item.task.category,
                    "Priority": st_item.task.priority.value,
                    "Duration": f"{st_item.duration_minutes} min",
                    "Why":      st_item.reason,
                })

            if rows:
                import pandas as pd
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)

            # Skipped tasks
            if scheduler.skipped:
                st.warning(
                    f"**{len(scheduler.skipped)} task(s) skipped** — exceeded daily time budget:"
                )
                for task, pet_name, reason in scheduler.skipped:
                    st.write(f"  - **{task.title}** ({pet_name}): {reason}")

            # Raw text summary (expandable)
            with st.expander("Raw schedule text"):
                st.code(scheduler.summary(), language="text")
