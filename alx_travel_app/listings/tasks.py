from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking

@shared_task
def send_booking_confirmation(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        send_mail(
            'Booking Confirmation',
            f'Your booking for {booking.listing.title} is confirmed.',
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            fail_silently=False,
        )
    except Booking.DoesNotExist:
        pass  # handle case where booking does not exist