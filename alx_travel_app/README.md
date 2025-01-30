# ALX Travel App (alx_travel_app_0x03)

## Overview
The **alx_travel_app_0x03** project extends the previous iterations by adding **background task management** using **Celery** and **RabbitMQ**. Additionally, it includes an **email notification system** for booking confirmations.

## Features
- **Django REST Framework API** for managing Listings and Bookings
- **MySQL Database** configuration with environment variables
- **Swagger API Documentation** for all endpoints
- **Celery and RabbitMQ Integration** for background task processing
- **Asynchronous Email Notifications** on booking creation

## Project Setup

### 1. Install Dependencies
Ensure you have all necessary dependencies installed:
```sh
pip install django djangorestframework mysqlclient celery drf-yasg django-environ
```

Install and start RabbitMQ:
```sh
sudo apt update && sudo apt install rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
```

### 2. Configure Celery

#### `alx_travel_app/celery.py`
Create a new file `celery.py` in the project root:
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')
app = Celery('alx_travel_app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

#### Modify `alx_travel_app/__init__.py`
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

#### Add Celery Config in `settings.py`
```python
CELERY_BROKER_URL = 'amqp://localhost'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

### 3. Implement Email Notification Task

#### `listings/tasks.py`
```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_booking_confirmation_email(to_email, booking_details):
    subject = "Booking Confirmation"
    message = f"Thank you for your booking. Details: {booking_details}"
    send_mail(subject, message, 'no-reply@yourdomain.com', [to_email])
    return f"Email sent to {to_email}"
```

### 4. Trigger Email Task on Booking Creation

#### Modify `listings/views.py`
```python
from rest_framework.viewsets import ModelViewSet
from .models import Booking
from .serializers import BookingSerializer
from .tasks import send_booking_confirmation_email

class BookingViewSet(ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        send_booking_confirmation_email.delay(booking.user.email, str(booking))
```

### 5. Running the Project

#### Start RabbitMQ
```sh
sudo systemctl start rabbitmq-server
```

#### Start Celery Worker
```sh
celery -A alx_travel_app worker --loglevel=info
```

#### Run Django Server
```sh
python manage.py runserver
```

#### Test the Email Task
Create a booking via Postman or Django Admin, and verify that the email is sent asynchronously.

## Repository Information
**GitHub Repository:** `alx_travel_app_0x03`
**Key Files:**
- `alx_travel_app/settings.py`
- `listings/tasks.py`
- `listings/views.py`
- `celery.py`
- `README.md`

---
This version of **alx_travel_app** enhances functionality by ensuring smooth background task management and improving user experience with automated email notifications. 

