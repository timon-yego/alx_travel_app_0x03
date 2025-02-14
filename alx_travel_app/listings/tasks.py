from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment

@shared_task
def send_payment_confirmation_email(payment_id):
    payment = Payment.objects.get(id=payment_id)
    subject = "Payment Confirmation"
    message = f"Dear {payment.user.first_name},\n\nYour payment of {payment.amount} ETB was successful!"
    recipient_list = [payment.user.email]

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

@shared_task
def send_booking_confirmation_email(email, booking_details):
    subject = "Booking Confirmation"
    message = f"Dear Customer,\n\nYour booking has been confirmed:\n\n{booking_details}\n\nThank you for choosing us!"
    sender = settings.DEFAULT_FROM_EMAIL

    send_mail(subject, message, sender, [email])

    return "Email sent successfully"

