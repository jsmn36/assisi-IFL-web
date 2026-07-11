---
trigger: always_on
---

SECTION 4 — STANDING QUERIES THE AGENT MUST ANSWER BEFORE EACH COMMIT
The agent must be able to answer YES to all of the following before committing:

Do all backend tests pass? (pytest tests/ -q --tb=short)
Do all frontend tests pass? (npm test -- --watchAll=false --silent)
Is backend coverage ≥80%? (pytest --cov=app --cov-fail-under=80)
Is mypy clean? (mypy app/ --strict)
Is flake8 clean? (flake8 . --max-line-length=100)
Is Black formatting applied? (black --check .)
Are there any direct ORM mutations to guarded models outside gates? (grep -r "\.save()\|db\.add\|db\.merge" app/services/ | grep -v gates)
Does the Alembic migration apply cleanly? (alembic upgrade head && alembic downgrade -1 && alembic upgrade head)
Are all new API endpoints registered in app/main.py and visible in /docs?
Is the commit message in the required format?

If the answer to any question is NO, fix it before committing.