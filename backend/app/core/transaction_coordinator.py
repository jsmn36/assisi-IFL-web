import logging
from typing import List, Dict, Any, Callable, Tuple
from sqlalchemy.orm import Session
from app.gates.base_gate import BaseGate
from app.gates.gate_executor import GateExecutor, GateExecutionResult

logger = logging.getLogger(__name__)


class TransactionCoordinator:
    """
    Ensures that all DB writes pass through the GateExecutor.
    Maintains atomicity: Rollbacks on failure, commits on success.
    """

    def __init__(self, db: Session):
        self.db = db
        self.executor = GateExecutor(db)

    def execute_write(
        self,
        gates: List[BaseGate],
        context: Dict[str, Any],
        action: Callable[[Session], Any],
    ) -> Tuple[bool, GateExecutionResult]:
        """
        Execute gates and if passed, run action and commit.

        Args:
            gates: Array of inherited BaseGate instances
            context: Shared state for gates
            action: Callback function that accepts (Session) and modifies DB. (Must NOT commit)

        Returns:
            Tuple containing boolean success and the GateExecutionResult trace.
        """
        # 1. Execute pre-flight verification
        result = self.executor.execute(gates, context, record_history=True)

        if result.has_blocking_failures:
            logger.warning(
                "Transaction aborted. Gate check failed: "
                f"{[r.message for r in result.get_failures()]}"
            )
            self.db.rollback()
            return False, result

        # 2. Execute bounded atomic write operation
        try:
            # Action should NOT call commit, only add/flush
            action(self.db)

            # 3. Final atomic commit containing both action + gate history log
            self.db.commit()
            return True, result

        except Exception as e:
            logger.error(f"Transaction action failed during database phase: {str(e)}")
            self.db.rollback()
            raise e
