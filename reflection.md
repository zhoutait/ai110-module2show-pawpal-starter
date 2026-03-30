# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

Based on the PawPal+ scenario, I identified three core actions a user should be able to perform:

Add and edit pet care tasks. The owner can create tasks (walks, feedings, meds, enrichment, grooming) and assign each a duration in minutes and a priority level (high, medium, low). They can also clear tasks and re-enter them as needs change.
Enter owner and pet information with constraints. The user provides their name, their pet's name/species/special needs, total available minutes for the day, and preferred task categories. These constraints feed directly into the scheduler.
Generate and view a daily care plan. Pressing one button produces a prioritized schedule that fits within the time budget. The app displays scheduled tasks in order, lists any deferred tasks, and explains each decision.

- What classes did you include, and what responsibilities did you assign to each?
I designed four classes:

Owner — holds name, available_time, preferences, and a list of Pet objects.
Pet — holds name, species, special_needs, and a list of Task objects.
Task — holds name, duration, priority, category, and a completion flag. Validates inputs on creation.
Scheduler — takes an Owner, collects all incomplete tasks across pets, sorts by priority (with a preference boost and shorter-duration tiebreak), then greedily packs tasks into the time budget. Tracks deferred tasks and generates a line-by-line explanation.

**b. Design changes**

- Did your design change during implementation?
Yes. 
- If yes, describe at least one change and why you made it.

The initial UML had Scheduler holding a flat all_tasks list as a stored attribute. During implementation I replaced that with a _collect_tasks() method that gathers tasks fresh from the Owner's pets each time generate_plan() is called. This avoids stale state if tasks are added or completed between scheduling runs. I also added a _preference_boost() helper that wasn't in the original UML — it became clear during testing that same-priority tasks needed a tiebreaker beyond just duration.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
The scheduler considers three constraints:

Time budget — total minutes the owner has available. No task can be scheduled if adding it would exceed this budget.
Priority — high > medium > low. Higher-priority tasks are always placed first.
Owner preferences — preferred categories get a small boost when two tasks share the same priority level.

- How did you decide which constraints mattered most?

I decided priority mattered most because the scenario describes a "busy pet owner" — when time is limited, critical tasks like medication should never be displaced by optional grooming.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
The scheduler uses a greedy algorithm: it sorts all tasks by priority and packs them sequentially. 
- Why is that tradeoff reasonable for this scenario?
This means it might skip a 30-minute medium-priority task even though two 15-minute low-priority tasks could have fit instead and provided more total coverage. I accepted this tradeoff because in pet care, doing the most important thing is almost always better than doing more things of lesser importance. A knapsack-style optimizer could technically pack more minutes, but it would sometimes schedule grooming over medication, which is the wrong call for this domain.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used AI to help with:

Brainstorming class responsibilities during initial design (e.g., should Scheduler own the tasks or collect them from Pet?).
Generating the boilerplate for the Streamlit UI layout.
Writing pytest-style test cases — I described the behaviors I wanted to test and iterated on edge cases.

- What kinds of prompts or questions were most helpful?
The most helpful prompts were specific and behavioral: "Write a test that proves completed tasks are excluded from the plan" worked much better than "Write tests for the scheduler."


**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
The AI initially suggested storing tasks inside the Scheduler constructor. I rejected this because it meant the Scheduler would hold a snapshot of tasks at creation time and wouldn't reflect tasks added later. 

- How did you evaluate or verify what the AI suggested?

I verified by mentally tracing a scenario: owner creates Scheduler, then adds a new task to the pet — the Scheduler would miss it. I refactored to the _collect_tasks() approach instead.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
I wrote 11 tests covering:

High-priority tasks are scheduled before low-priority ones.
Total scheduled time never exceeds the time budget.
Low-priority tasks are deferred when time is short.
Empty task lists produce an empty plan.
Completed tasks are excluded.
Preferred categories break ties among same-priority tasks.
The explanation string mentions every task.
Zero available time defers everything.
Tasks that exactly fill the budget are all scheduled.
Invalid priority or negative duration raise ValueError.

- Why were these tests important?

These tests matter because they validate the core contract of the scheduler: it should always respect priority ordering, never exceed the time budget, and correctly explain its decisions.

**b. Confidence**

- How confident are you that your scheduler works correctly?
I am fairly confident the scheduler works correctly for single-pet scenarios

- What edge cases would you test next if you had more time?

Edge cases I would test next with more time:

Multiple pets with competing high-priority tasks.
Tasks with identical priority, category, and duration (tie-breaking stability).
Very large task lists (performance).
Tasks with zero duration (should they be allowed?).



---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
The greedy scheduling algorithm turned out to be simple to implement and easy to explain. The explain_plan() method was straightforward because the scheduler already tracks every decision it makes during the packing loop. The UML-first approach helped — having the class diagram before coding meant I rarely had to rethink where data belonged.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would add the ability to edit or delete individual tasks in the Streamlit UI (right now you can only clear all and re-enter). I would also explore a time-slot model where tasks are pinned to specific hours (e.g., medication at 8 AM, walk at 6 PM) rather than just ordered in a flat list.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Designing the system on paper first — even a rough UML — saved significant time during implementation. The biggest wins came not from getting the diagram perfect, but from forcing myself to decide which class owns which data before writing any code. When I skipped that step mentally, I ended up with tangled logic that had to be refactored.
## 6. AI Strategy Reflection

**a. Effective Copilot Features**
The most effective Copilot features for building the scheduler were Inline Chat and the Generate Tests smart action. Inline Chat allowed me to quickly ask for specific algorithmic implementations, such as how to use a lambda function to sort tasks by time, without losing context of the file I was working in. The Generate Tests feature significantly sped up the creation of boilerplate test code, allowing me to focus on defining the edge cases rather than writing repetitive setup code.

**b. Rejected AI Suggestion**
During the implementation of the conflict detection algorithm, Copilot suggested a complex interval tree approach to handle overlapping times. I rejected this suggestion because it was overly complex for the scale of a daily pet schedule (which typically has fewer than 20 tasks). Instead, I opted for a simpler nested loop approach that checks for overlaps directly. This kept the system design clean, readable, and easy to maintain, which is more important than micro-optimizations for this specific use case.

**c. Organizing with Separate Chat Sessions**
Using separate chat sessions for different phases (e.g., one for core implementation, one for algorithmic logic, and one for testing) was crucial for staying organized. It prevented the AI's context window from becoming cluttered with irrelevant code or previous discussions. For example, when I started the testing phase, starting a new session ensured that Copilot focused entirely on generating test cases based on the final implementation, rather than getting confused by earlier drafts of the code.

**d. Lead Architect Summary**
Collaborating with powerful AI tools taught me that the role of a developer is shifting from "code writer" to "lead architect." The AI is excellent at generating syntax, suggesting algorithms, and writing boilerplate, but it lacks the domain knowledge and high-level vision to make architectural tradeoffs. As the lead architect, my primary responsibility is to define clear constraints, evaluate the AI's suggestions against the project's goals, and ensure the final system remains cohesive and maintainable. The AI is a powerful assistant, but human judgment is still required to build a truly robust system.
