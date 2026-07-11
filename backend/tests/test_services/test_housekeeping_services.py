"""
Test Housekeeping Services
"""
import pytest
from datetime import date, time, timedelta
from app.services import HousekeepingService, MaintenanceService
from app.services.workflow_automation_service import WorkflowAutomationService
from app.models import (
    Property,
    RoomType,
    Room,
    RoomStatus,
    User,
    HousekeepingTask,
    TaskType,
    TaskStatus,
    TaskPriority,
    MaintenanceRequest,
    Stay,
    StayStatus,
    Guest,
    Reservation,
)
from decimal import Decimal


@pytest.fixture
def setup_housekeeping_test_data(test_db):
    """Setup test data for housekeeping tests"""
    property = Property(
        name="Housekeeping Hotel",
        code="HK",
        address_line1="123",
        city="C",
        state="S",
        postal_code="12345",
    )
    test_db.add(property)
    test_db.commit()

    room_type = RoomType(
        property_id=property.id,
        code="STD",
        name="Standard",
        base_price=Decimal("100"),
        max_occupancy=2,
        max_adults=2,
        max_children=1,
    )
    test_db.add(room_type)
    test_db.commit()

    room1 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="101",
        status=RoomStatus.DIRTY,
    )
    room2 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="102",
        status=RoomStatus.CLEAN,
    )
    test_db.add_all([room1, room2])
    test_db.commit()

    user = User(
        username="housekeeper1",
        email="hk1@test.com",
        hashed_password="hash",
        role="housekeeper",
    )
    test_db.add(user)
    test_db.commit()

    return property, room_type, room1, room2, user


def test_create_housekeeping_task(test_db, setup_housekeeping_test_data):
    """Test creating housekeeping task"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    service = HousekeepingService(test_db)
    task = service.create_task(
        property_id=property.id,
        room_id=room1.id,
        task_type=TaskType.CHECKOUT_CLEANING,
        scheduled_date=date.today(),
        priority=TaskPriority.HIGH,
        created_by="manager",
    )

    assert task.task_type == TaskType.CHECKOUT_CLEANING
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.PENDING
    assert task.estimated_duration == 30


def test_assign_task(test_db, setup_housekeeping_test_data):
    """Test assigning task to staff"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    service = HousekeepingService(test_db)
    task = service.create_task(
        property_id=property.id,
        room_id=room1.id,
        task_type=TaskType.STAYOVER_CLEANING,
        scheduled_date=date.today(),
        created_by="manager",
    )

    assigned_task = service.assign_task(task.id, user.id, "manager")

    assert assigned_task.assigned_to == user.id
    assert assigned_task.status == TaskStatus.ASSIGNED
    assert assigned_task.assigned_at is not None


def test_complete_task_workflow(test_db, setup_housekeeping_test_data):
    """Test complete task workflow"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    service = HousekeepingService(test_db)

    task = service.create_task(
        property_id=property.id,
        room_id=room1.id,
        task_type=TaskType.CHECKOUT_CLEANING,
        scheduled_date=date.today(),
        created_by="manager",
    )
    service.assign_task(task.id, user.id, "manager")

    started = service.start_task(task.id, "housekeeper1")
    assert started.status == TaskStatus.IN_PROGRESS
    assert started.started_at is not None
    assert room1.status == RoomStatus.CLEANING

    completed = service.complete_task(task.id, "All clean", "housekeeper1")
    assert completed.status == TaskStatus.COMPLETED
    assert completed.completed_at is not None
    assert completed.actual_duration is not None
    assert room1.status == RoomStatus.CLEAN


def test_inspect_task(test_db, setup_housekeeping_test_data):
    """Test task inspection"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    inspector = User(
        username="inspector",
        email="inspector@test.com",
        hashed_password="hash",
        role="inspector",
    )
    test_db.add(inspector)
    test_db.commit()

    service = HousekeepingService(test_db)

    task = service.create_task(
        property_id=property.id,
        room_id=room1.id,
        task_type=TaskType.CHECKOUT_CLEANING,
        scheduled_date=date.today(),
        created_by="manager",
    )
    service.assign_task(task.id, user.id, "manager")
    service.start_task(task.id, "housekeeper1")
    service.complete_task(task.id, notes="Done", completed_by="housekeeper1")

    inspected = service.inspect_task(task.id, True, inspector.id, "Looks good")
    assert inspected.status == TaskStatus.INSPECTED
    assert inspected.inspection_passed is True
    assert room1.status == RoomStatus.AVAILABLE


def test_inspect_task_failed(test_db, setup_housekeeping_test_data):
    """Test failed inspection"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    inspector = User(
        username="inspector2",
        email="inspector2@test.com",
        hashed_password="hash",
        role="inspector",
    )
    test_db.add(inspector)
    test_db.commit()

    service = HousekeepingService(test_db)

    task = service.create_task(
        property_id=property.id,
        room_id=room1.id,
        task_type=TaskType.CHECKOUT_CLEANING,
        scheduled_date=date.today(),
        created_by="manager",
    )
    service.assign_task(task.id, user.id, "manager")
    service.start_task(task.id, "housekeeper1")
    service.complete_task(task.id, completed_by="housekeeper1")

    inspected = service.inspect_task(task.id, False, inspector.id, "Bathroom not clean")
    assert inspected.status == TaskStatus.FAILED_INSPECTION
    assert inspected.inspection_passed is False
    assert room1.status == RoomStatus.DIRTY


def test_create_maintenance_request(test_db, setup_housekeeping_test_data):
    """Test creating maintenance request"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    service = MaintenanceService(test_db)
    request = service.create_request(
        property_id=property.id,
        title="Broken AC",
        description="AC not cooling properly",
        category="hvac",
        priority=TaskPriority.HIGH,
        room_id=room1.id,
        reported_by="guest",
        created_by="frontdesk",
    )

    assert request.title == "Broken AC"
    assert request.category == "hvac"
    assert request.priority == TaskPriority.HIGH
    assert request.status == "pending"


def test_maintenance_workflow(test_db, setup_housekeeping_test_data):
    """Test complete maintenance workflow"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    technician = User(
        username="tech1",
        email="tech@test.com",
        hashed_password="hash",
        role="technician",
    )
    test_db.add(technician)
    test_db.commit()

    service = MaintenanceService(test_db)

    request = service.create_request(
        property_id=property.id,
        title="Leaky faucet",
        description="Bathroom faucet dripping",
        category="plumbing",
        priority=TaskPriority.NORMAL,
        room_id=room1.id,
        created_by="frontdesk",
    )

    assigned = service.assign_request(
        request.id, technician.id, date.today(), "manager"
    )
    assert assigned.status == "assigned"
    assert assigned.assigned_to == technician.id

    started = service.start_work(request.id, "tech1")
    assert started.status == "in_progress"

    completed = service.complete_work(
        request.id, "Replaced washer, fixed leak", Decimal("25.50"), "tech1"
    )
    assert completed.status == "completed"
    assert completed.actual_cost == 2550


def test_workflow_automation(test_db, setup_housekeeping_test_data):
    """Test workflow automation"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    guest = Guest(first_name="Test", last_name="Guest", email="test@test.com")
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="AUTO-001",
        check_in_date=date.today() - timedelta(days=1),
        check_out_date=date.today(),
        number_of_nights=1,
        num_adults=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("100"),
    )
    test_db.add(reservation)
    test_db.commit()

    stay = Stay(
        property_id=property.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room1.id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        num_adults=2,
        nightly_rate=Decimal("100"),
        status=StayStatus.CHECKED_IN,
    )
    test_db.add(stay)
    test_db.commit()

    service = WorkflowAutomationService(test_db)
    result = service.process_daily_housekeeping(property.id, date.today(), "automation")

    assert result["checkout"] >= 1
    assert result["total"] >= 1


def test_auto_assign_tasks(test_db, setup_housekeeping_test_data):
    """Test auto-assignment"""
    property, room_type, room1, room2, user = setup_housekeeping_test_data

    hk_service = HousekeepingService(test_db)
    task_types = [
        TaskType.CHECKOUT_CLEANING,
        TaskType.STAYOVER_CLEANING,
        TaskType.DEEP_CLEANING,
    ]
    for i in range(3):
        hk_service.create_task(
            property_id=property.id,
            room_id=room1.id if i % 2 == 0 else room2.id,
            task_type=task_types[i],
            scheduled_date=date.today(),
            created_by="manager",
        )

    from app.models import HousekeepingStaff

    staff = HousekeepingStaff(
        property_id=property.id, user_id=user.id, role="housekeeper"
    )
    test_db.add(staff)
    test_db.commit()

    result = hk_service.auto_assign_tasks(property.id, date.today(), "manager")

    assert result["assigned"] == 3
    assert result["staff_count"] == 1
