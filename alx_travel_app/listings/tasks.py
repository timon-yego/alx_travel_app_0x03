from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_booking_confirmation_email(to_email, booking_details):
    subject = "Booking Confirmation"
    message = f"Thank you for your booking. Details: {booking_details}"
    send_mail(subject, message, 'no-reply@yourdomain.com', [to_email])
    return f"Email sent to {to_email}"
