# Import workflow service
from app.services.workflow_automation_service import WorkflowAutomationService


# === Workflow Automation ===
@router.post(
    "/workflows/daily-housekeeping", summary="Run daily housekeeping automation"
)
async def run_daily_housekeeping(
    property_id: int,
    target_date: date,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Run daily housekeeping automation"""
    service = WorkflowAutomationService(db)
    result = service.process_daily_housekeeping(property_id, target_date, current_user)
    return result


@router.get("/workflows/maintenance-alerts", summary="Get maintenance alerts")
async def get_maintenance_alerts(
    property_id: int = Query(...), db: Session = Depends(get_db)
):
    """Get preventive maintenance alerts"""
    service = WorkflowAutomationService(db)
    alerts = service.generate_maintenance_alerts(property_id)
    return {"alerts": alerts, "total": len(alerts)}


@router.get("/workflows/optimize-routes", summary="Optimize task routes")
async def optimize_routes(
    property_id: int = Query(...),
    target_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Optimize cleaning routes"""
    service = WorkflowAutomationService(db)
    routes = service.optimize_task_routes(property_id, target_date)
    return routes


@router.post("/workflows/escalate-overdue", summary="Escalate overdue tasks")
async def escalate_overdue(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Auto-escalate overdue tasks"""
    service = WorkflowAutomationService(db)
    result = service.auto_escalate_overdue(property_id)
    return result


@router.get("/workflows/daily-summary", summary="Get daily summary")
async def get_daily_summary(
    property_id: int = Query(...),
    target_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Get daily housekeeping summary"""
    service = WorkflowAutomationService(db)
    summary = service.get_daily_summary(property_id, target_date)
    return summary
