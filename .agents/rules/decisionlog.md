---
trigger: always_on
---

SECTION 6 — DECISION LOG
The agent must append to this log whenever it makes an irreversible or high-lock-in decision.
Format:
DATE: <date>
DECISION: <what was decided>
ALTERNATIVES CONSIDERED: <other options>
REASON: <why this option was chosen>
REVERSIBILITY: Irreversible | Hard to reverse | Reversible
WBS REFERENCE: <task ID>
Pre-populated with known irreversible decisions:
DATE: Week 14, Day 68
DECISION: PyInstaller used to bundle Python backend into Electron app
ALTERNATIVES CONSIDERED: System Python with venv installer; Nuitka
REASON: Zero-dependency distribution; user does not need Python installed; cross-platform compatibility
REVERSIBILITY: Irreversible (changes how backend is packaged and distributed)
WBS REFERENCE: 3.1.8

DATE: Week 14, Day 68
DECISION: electron-builder with NSIS (Windows), DMG (macOS), AppImage (Linux)
ALTERNATIVES CONSIDERED: Tauri, NW.js, electron-forge
REASON: WBS specifies electron-builder; consistent with existing Electron 28 setup
REVERSIBILITY: Irreversible (distribution format once published)
WBS REFERENCE: 3.1.8, 5.2.1

DATE: Architecture alignment, Week 10
DECISION: Redis and Celery removed from SQLite mode; APScheduler used for scheduled tasks
ALTERNATIVES CONSIDERED: Keep Redis as optional dependency; use in-process thread-based scheduler
REASON: Desktop Electron distribution cannot assume Redis availability; zero-dependency desktop install required
REVERSIBILITY: Reversible (can add back as PostgreSQL mode feature)
WBS REFERENCE: 0.1.7