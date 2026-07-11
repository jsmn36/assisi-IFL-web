# Email Templates Documentation

## Overview

The Hotel PMS uses a professional email template system built on Jinja2 for all outgoing communications.

## Features

- **Professional Design**: Beautiful, responsive HTML templates
- **Plain Text Support**: Automatic plain text fallback
- **Template Inheritance**: Base template with consistent branding
- **Dynamic Content**: Variable substitution and custom filters
- **CSS Inlining**: Automatic CSS inlining for email client compatibility
- **Preview System**: Test templates before sending
- **User Preferences**: Respect user notification settings

## Available Templates

### Reservations
- `reservation_confirmation.html` - Booking confirmation
- `checkin_reminder.html` - Day before check-in
- `checkout_reminder.html` - Day before check-out
- `reservation_cancelled.html` - Cancellation confirmation

### Payments
- `payment_receipt.html` - Payment confirmation with receipt

### System
- `password_reset.html` - Password reset link
- `account_created.html` - New account welcome
- `daily_report.html` - Daily performance summary

### Guest Communication
- `welcome_guest.html` - Check-in welcome
- `thank_you.html` - Post-stay thank you

### Marketing
- `promotion.html` - Special offers and promotions

## Template Structure

### Base Template (base.html)

All templates extend the base template:
```html
{% extends "base.html" %}

{% block title %}Your Page Title{% endblock %}
{% block header %}Your Header{% endblock %}
{% block content %}
  Your content here
{% endblock %}
```

### Components

**Info Box:**
```html
<div class="info-box">
    <h3>Title</h3>
    <table>
        <tr>
            <td>Label:</td>
            <td>Value</td>
        </tr>
    </table>
</div>
```

**Button:**
```html
<center>
    <a href="{{ url }}" class="button">Click Here</a>
</center>
```

## Custom Filters

### Currency Filter
```
{{ amount|currency }}
# Output: $1,234.56
```

### Date Filter
```
{{ date_field|date }}
# Output: January 24, 2024
```

### DateTime Filter
```
{{ timestamp|datetime }}
# Output: January 24, 2024 at 3:45 PM
```

## Usage

### Send Template Email
```python
from app.services.enhanced_email_service import EnhancedEmailService

service = EnhancedEmailService(db)

service.send_template_email(
    to_email="guest@example.com",
    template_name="reservation_confirmation",
    context={
        "guest_name": "John Doe",
        "confirmation_code": "ABC123",
        # ... other variables
    },
    subject="Reservation Confirmation",
    notification_type="reservation_confirmation"
)
```

### Preview Template
```python
preview = service.preview_template(
    template_name="reservation_confirmation",
    context={...}
)

print(preview["html"])  # Rendered HTML
print(preview["text"])  # Rendered text
```

### Check Required Variables
```python
from app.services.template_service import template_service

variables = template_service.get_template_variables(
    "reservation_confirmation.html"
)
print(variables)  # ['guest_name', 'confirmation_code', ...]
```

## API Endpoints

### List Templates
```
GET /api/v1/email-templates/list
```

### Get Template Variables
```
GET /api/v1/email-templates/variables/{template_name}
```

### Preview Template
```
POST /api/v1/email-templates/preview
{
  "template_name": "reservation_confirmation",
  "context": {...}
}
```

### Send Test Email
```
POST /api/v1/email-templates/test-send
{
  "template_name": "reservation_confirmation",
  "to_email": "test@example.com",
  "context": {...}
}
```

### Get Sample Data
```
GET /api/v1/email-templates/sample-data/{template_name}
```

## Notification Preferences

Users can control which emails they receive:
```
# Get preferences
GET /api/v1/notification-preferences

# Update preferences
PUT /api/v1/notification-preferences
{
  "reservation_confirmation": true,
  "promotional_emails": false
}

# Unsubscribe
POST /api/v1/notification-preferences/unsubscribe/promotional_emails
```

## Creating New Templates

1. Create HTML template in `app/templates/emails/`:
```html
{% extends "base.html" %}

{% block title %}My New Template{% endblock %}
{% block header %}Header Text{% endblock %}

{% block content %}
<h2>Hello, {{ user_name }}!</h2>
<p>Your content here with {{ variables }}.</p>
{% endblock %}
```

2. Create text version (optional):
```
{% extends "base.txt" %}

{% block content %}
Hello, {{ user_name }}!

Your content here with {{ variables }}.
{% endblock %}
```

3. Add helper method in `EmailTemplates` class:
```python
@staticmethod
def send_my_new_email(db: Session, user_id: int, to_email: str):
    context = {
        "user_name": "...",
        # ...
    }
    
    service = EnhancedEmailService(db)
    return service.send_template_email(
        to_email=to_email,
        template_name="my_new_template",
        context=context,
        subject="My Subject"
    )
```

4. Create background task:
```python
@shared_task(bind=True, base=RetryTask, queue='emails')
def send_my_new_email_task(self, user_id: int):
    # Implementation
    pass
```

## Best Practices

- **Always provide plain text**: Some email clients only show text
- **Keep it simple**: Complex layouts may break in email clients
- **Test thoroughly**: Use preview before sending
- **Respect preferences**: Always check notification settings
- **Use inline CSS**: Email clients don't support external stylesheets
- **Mobile first**: Design for mobile, enhance for desktop
- **Clear CTA**: Make calls-to-action obvious
- **Avoid images**: Use sparingly, many clients block by default

## Troubleshooting

### Template Not Found
- Check template name spelling
- Ensure file is in `app/templates/emails/`
- Check file extension (`.html` or `.txt`)

### Variables Not Rendering
- Ensure context includes all required variables
- Check variable names match template
- Use `get_template_variables()` to verify

### Styling Issues
- CSS must be inline (happens automatically)
- Test in multiple email clients
- Keep layouts simple

### Emails Not Sending
- Check SMTP configuration
- Verify notification preferences
- Check logs for errors
- Test with simple template first
