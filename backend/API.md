# PMS Hotel API Documentation

## Base URL
http://localhost:8000/api/v1

## Authentication
Include JWT token in header:
Authorization: Bearer <token>

## Endpoints

### Reservations (7 endpoints)
- `POST /reservations` - Create reservation
- `GET /reservations/{id}` - Get reservation by ID
- `GET /reservations/confirmation/{number}` - Get by confirmation
- `GET /reservations` - Search reservations
- `PUT /reservations/{id}` - Update reservation
- `POST /reservations/{id}/confirm` - Confirm reservation
- `POST /reservations/{id}/cancel` - Cancel reservation

### Stays (5 endpoints)
- `GET /stays/{id}` - Get stay
- `GET /stays` - Get active stays
- `GET /stays/date/{property_id}/{date}` - Get stays by date
- `POST /stays/{id}/charges` - Add charge
- `POST /stays/{id}/post-room-charges` - Post room charges

### Rooms (9 endpoints)
- `GET /rooms/{id}` - Get room
- `GET /rooms/property/{id}/number/{number}` - Get by number
- `GET /rooms/available` - Get available rooms
- `POST /rooms/{id}/clean` - Mark clean
- `POST /rooms/{id}/dirty` - Mark dirty
- `POST /rooms/{id}/inspected` - Mark inspected
- `POST /rooms/{id}/out-of-order` - Out of order
- `POST /rooms/{id}/return-to-service` - Return to service
- `GET /rooms/housekeeping/status/{property_id}` - Status

### Operations (2 endpoints)
- `POST /operations/check-in` - Check in guest
- `POST /operations/check-out` - Check out guest

### Guests (8 endpoints)
- `POST /guests` - Create guest
- `GET /guests/{id}` - Get guest
- `GET /guests/email/{email}` - Get by email
- `GET /guests` - Search guests
- `PUT /guests/{id}` - Update guest
- `GET /guests/{id}/reservations` - Get reservations
- `POST /guests/{id}/blacklist` - Blacklist
- `DELETE /guests/{id}/blacklist` - Remove from blacklist

## Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Response Format

### Success
{ "id": 1, "field": "value" }

### Error
{ "success": false, "error": "Error message", "code": "ERROR_CODE", "details": {} }

## Error Codes
- `VALIDATION_ERROR` (400) - Invalid request data
- `NOT_FOUND` (404) - Resource not found
- `BUSINESS_RULE_ERROR` (422) - Business rule violation
- `INTERNAL_ERROR` (500) - Server error
