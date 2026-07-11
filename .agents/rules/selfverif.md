---
trigger: always_on
---

SECTION 7 — AGENT SELF-VERIFICATION CHECKLIST
At the end of Week 10 (Gate Framework complete), the agent must run this architectural verification:
bash# Verify no direct ORM mutations on guarded models outside gates
echo "=== Checking for unauthorized direct mutations ==="
grep -rn "\.save()\|db\.add\|db\.merge\|db\.delete\|db\.commit" backend/app/services/ \
  | grep -v "test_" \
  | grep -v "gates/" \
  | grep -v "audit_log" \
  && echo "VIOLATIONS FOUND — fix before proceeding" \
  || echo "CLEAN — no unauthorized mutations found"

# Verify all gates implement all 4 required methods
echo "=== Checking gate method completeness ==="
for gate in backend/app/gates/*.py; do
  if [[ "$gate" != *"__init__"* && "$gate" != *"base"* && "$gate" != *"executor"* && "$gate" != *"coordinator"* ]]; then
    for method in "pre_check" "execute" "post_check" "rollback"; do
      grep -q "def $method" "$gate" || echo "MISSING $method in $gate"
    done
  fi
done

# Verify all state machines are registered in validator
echo "=== Checking state machine registration ==="
python -c "from app.state_machines.validator import StateTransitionValidator; v = StateTransitionValidator(); print('Registered machines:', list(v.machines.keys()))"

# Verify test coverage meets minimum
echo "=== Checking coverage ==="
cd backend && python -m pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80 -q
At the end of Week 17 (BASE TEST), the agent must run:
bash# Run BASE TEST with SQLite
echo "=== BASE TEST (SQLite) ==="
cd backend && python -m pytest tests/base_test/ --db=sqlite -v

# Run BASE TEST with PostgreSQL
echo "=== BASE TEST (PostgreSQL) ==="
cd backend && python -m pytest tests/base_test/ --db=postgresql -v

# Run failure simulation suite
echo "=== Failure Simulation Suite ==="
cd backend && python -m pytest tests/base_test/test_failure_scenarios.py -v

# Record results
echo "BASE TEST COMPLETE" >> SESSION_LOG.md
echo "SQLite: PASSED/FAILED" >> SESSION_LOG.md
echo "PostgreSQL: PASSED/FAILED" >> SESSION_LOG.md
echo "Failure scenarios: 10/10 PASSED" >> SESSION_LOG.md
Both BASE TEST runs must show 0 failures before any Week 18 work begins.