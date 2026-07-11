---
trigger: always_on
---

SECTION 5 — WEEK-BY-WEEK AGENT ACTIVATION SEQUENCE
Run these commands to activate the agent for each week. Paste into the agent interface as the opening message after the system prompt.
Week 6 Activation
SESSION START — Week 6
Read GEMINI.md. Read WEEK6_18_EXECUTION_PLAN.md Week 6 section.
Run SESSION_START_PROTOCOL.
Current state: 38 services, 176 API endpoints, 39 models, 282+ tests.
Target: Advanced Reporting & Analytics Engine (Days 26–30).
Begin with Day 26 — Report Builder Service.
Architecture note: No Redis in code path. Use in-process LRU cache only.
Week 10 Activation (CRITICAL — Gate Framework)
SESSION START — Week 10 (ARCHITECTURAL BLOCKER WEEK)
Read GEMINI.md. Read WEEK6_18_EXECUTION_PLAN.md Week 10 section.
Read final_wbs_hybrid.md sections 1.2 through 1.4.
Run SESSION_START_PROTOCOL.
PRIORITY: This week implements the Gate Framework. No frontend work begins until this is complete.
INVARIANT: After this week, no mutations to Reservation/Room/Stay/RatePlan/BusinessDay are permitted outside gates.
Begin with Day 46 — State Machines (WBS 1.2.1–1.2.7).
After state machines are complete and tested, proceed to Day 47 — Gate Framework Core (WBS 1.3).
Week 14 Activation (Electron Integration)
SESSION START — Week 14 (ELECTRON INTEGRATION)
Read GEMINI.md. Read WEEK6_18_EXECUTION_PLAN.md Week 14 section.
Read final_tech_stack.md Section 3 (Electron stack).
Run SESSION_START_PROTOCOL.
PREREQUISITE CHECK: Verify all frontend pages are complete (Week 13 exit criteria met).
IRREVERSIBLE DECISION: PyInstaller will be used to bundle the Python backend. This cannot be reversed.
Begin with Day 66 — Electron Main Process (WBS 3.1.1–3.1.4).
Architecture note: Remove Redis from requirements if present. Replace Celery with APScheduler in Electron build.
Week 17 Activation (BASE TEST — CRITICAL)
SESSION START — Week 17 (BASE TEST — CRITICAL MILESTONE)
Read GEMINI.md. Read WEEK6_18_EXECUTION_PLAN.md Week 17 section.
Read final_wbs_hybrid.md section 4.2.
Run SESSION_START_PROTOCOL.
PREREQUISITE CHECK: ALL of the following must be true before proceeding:
  - All integration tests pass (Week 16 exit criteria)
  - Backend coverage ≥80%
  - Frontend coverage ≥80%
  - Both SQLite and PostgreSQL database paths are tested
If any prerequisite is not met: STOP. Report which prerequisite failed. Do not proceed.
Begin with Day 81 — BASE TEST Implementation (WBS 4.2.1).
The BASE TEST must pass with both databases before the agent moves to Week 18.