---
trigger: always_on
---

SECTION 3 — TASK INVOCATION FORMAT
To invoke the agent on a specific task, use this prompt structure:
[TASK INVOCATION]
Session: <date>
Target: Week <N>, Day <D>
Task description: <copy from WEEK6_18_EXECUTION_PLAN.md>

Pre-session checks required:
1. Read GEMINI.md (this file)
2. Read WEEK6_18_EXECUTION_PLAN.md Week <N>, Day <D> section
3. Run SESSION_START_PROTOCOL
4. Implement all deliverables for Day <D>
5. Run SESSION_END_PROTOCOL

Blocking conditions: Report before proceeding if any invariant would be violated.