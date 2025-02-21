from django.shortcuts import render
from rest_framework import viewsets, status
from .models import Listing, Booking, Review, Payment
from .serializers import ListingSerializer, BookingSerializer, ReviewSerializer, PaymentSerializer
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .tasks import send_payment_confirmation_email
from .tasks import send_booking_confirmation_email

# Create your views here.
class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class BookingViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()

        # Extract guest details
        email = booking.guest_email  # Ensure Booking model has `guest_email`

        # Send booking confirmation email
        booking_details = f"Listing: {booking.listing.title}, Check-in: {booking.check_in}, Check-out: {booking.check_out}, Price: {booking.listing.price_per_night}"
        send_booking_confirmation_email.delay(email, booking_details)

        return Response(
            {"message": "Booking created successfully. Proceed to payment."},
            status=status.HTTP_201_CREATED
        )

class InitiatePaymentView(APIView):
    """
    Handles payment initiation for an existing booking.
    """
    def post(self, request):
        booking_id = request.data.get("booking_id")
        email = request.data.get("email")
        phone_number = request.data.get("phone_number")

        # Fetch booking using provided details
        if booking_id:
            booking = get_object_or_404(Booking, id=booking_id)
        elif email and phone_number:
            booking = get_object_or_404(Booking, guest_email=email, guest_phone=phone_number)
        else:
            return Response(
                {"error": "Provide either a Booking ID or both email and phone number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract payment details
        amount = booking.listing.price_per_night
        transaction_id = f"{booking.id}-{int(booking.created_at.timestamp())}"
        booking_reference = f"BOOK-{booking.id}"

        # Ensure no duplicate payment entry
        payment, created = Payment.objects.get_or_create(
            booking_reference=booking_reference,
            defaults={
                "transaction_id": transaction_id,
                "amount": amount,
                "status": "Pending",
            }
        )

        if not created:
            return Response({"error": "Payment already initiated for this booking."}, status=status.HTTP_400_BAD_REQUEST)


        # Initiate Chapa Payment
        chapa_payload = {
            "amount": amount,
            "currency": "ETB",
            "email": email,
            "tx_ref": transaction_id,
            "return_url": "http://yourfrontend.com/payment-success",
            "callback_url": "http://yourbackend.com/api/payments/verify-payment/",
            "customization": {
                "title": "Booking Payment",
                "description": f"Payment for booking ID {booking.id}",
            },
        }

        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        response = requests.post(f"{settings.CHAPA_BASE_URL}/transaction/initialize", json=chapa_payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            payment.transaction_id = data["data"]["tx_ref"]
            payment.save()
            return Response({"checkout_url": data["data"]["checkout_url"]}, status=status.HTTP_201_CREATED)
        else:
            payment.status = "Failed"
            payment.save()
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)


class VerifyPaymentView(APIView):
    """
    Verifies payment status with Chapa and updates the database.
    """
    def get(self, request):
        transaction_id = request.query_params.get("transaction_id")
        if not transaction_id:
            return Response({"error": "Transaction ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        response = requests.get(f"{settings.CHAPA_BASE_URL}/transaction/verify/{transaction_id}", headers=headers)

        if response.status_code == 200:
            data = response.json()
            payment = get_object_or_404(Payment, transaction_id=transaction_id)

            if data["data"]["status"] == "success":
                payment.status = "Completed"
                payment.save()

                # Send payment confirmation email
                if payment.email_address:
                    send_payment_confirmation_email.delay(payment.email_address, payment.amount, payment.booking.id)

                return Response({"status": "Payment successful. Confirmation email sent."}, status=status.HTTP_200_OK)

            else:
                payment.status = "Failed"
                payment.save()
                return Response({"status": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)