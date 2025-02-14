Milestone 2: Database Modeling and Data Seeding in Django

# Milestone 3: Creating Views and API Endpoints
API Development for Listings and Bookings in Django
Build API views to manage listings and bookings, and ensure the endpoints are documented with Swagger.

## API Endpoints

### Listings

- `GET /api/listings/` – Retrieve a list of all listings
- `POST /api/listings/` – Create a new listing
- `GET /api/listings/{id}/` – Retrieve a specific listing
- `PUT /api/listings/{id}/` – Update a listing
- `DELETE /api/listings/{id}/` – Delete a listing

### Bookings

- `GET /api/bookings/` – Retrieve a list of all bookings
- `POST /api/bookings/` – Create a new booking
- `GET /api/bookings/{id}/` – Retrieve a specific booking
- `PUT /api/bookings/{id}/` – Update a booking
- `DELETE /api/bookings/{id}/` – Delete a booking

# Milestone 4: Payment Integration with Chapa API
## Payment Integration (Chapa API)

This project integrates the Chapa API for payment processing.

### Payment Endpoints:
- `POST /api/payments/initiate/` - Initiates a payment.
- `GET /api/payments/verify/` - Verifies a payment.

### Setup:
1. Add `CHAPA_SECRET_KEY` to `.env`.
2. Run `python manage.py migrate` to apply payment model.
3. Start Celery: `celery -A alx_travel_app worker --loglevel=info`.

### Testing:
Use Chapa sandbox mode for testing payments.

# Milestone 5
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
