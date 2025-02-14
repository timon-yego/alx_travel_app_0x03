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

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()

    def perform_create(self, serializer):
        booking = serializer.save(user=self.request.user)
        
        # Automatically initiate payment
        transaction_id = f"{self.request.user.id}-{booking.id}-{int(booking.created_at.timestamp())}"
        amount = booking.listing.price  # Assuming price exists on Listing model

        payment = Payment.objects.create(
            user=self.request.user,
            booking=booking,
            transaction_id=transaction_id,
            amount=amount,
            status="Pending",
        )

        # Trigger Celery email task
        booking_details = f"Listing: {booking.listing.title}, Date: {booking.date}, Price: {booking.price}"
        send_booking_confirmation_email.delay(self.request.user.email, booking_details)

        return payment.transaction_id


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def post(self, request):
        """
        Initiates a payment and returns a checkout URL from Chapa.
        """
        user = request.user
        amount = request.data.get('amount')
        booking_reference = request.data.get('booking_reference')

        if not amount or not booking_reference:
            return Response({"error": "Amount and booking reference are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a Payment entry
        payment = Payment.objects.create(user=user, amount=amount, booking_reference=booking_reference)

        chapa_payload = {
            "amount": amount,
            "currency": "USD",
            "email": user.email,
            "tx_ref": booking_reference,
            "return_url": "http://yourfrontend.com/payment-success",
            "callback_url": "http://yourbackend.com/api/payments/verify-payment/",
            "customization": {
                "title": "Booking Payment",
                "description": "Payment for travel booking"
            }
        }

        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        response = requests.post(f"{settings.CHAPA_BASE_URL}/transaction/initialize", json=chapa_payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            payment.transaction_id = data["data"]["tx_ref"]
            payment.save()
            return Response({"checkout_url": data["data"]["checkout_url"]}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)

class VerifyPaymentView(APIView):
    """
    Handles payment verification with Chapa API.
    """

    def get(self, request):
        """
        Verifies the payment status using the transaction ID.
        """
        transaction_id = request.query_params.get('transaction_id')
        if not transaction_id:
            return Response({"error": "Transaction ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        response = requests.get(f"{settings.CHAPA_BASE_URL}/transaction/verify/{transaction_id}", headers=headers)

        if response.status_code == 200:
            data = response.json()
            payment = get_object_or_404(Payment, transaction_id=transaction_id)

            if data["data"]["status"] == "success":
                payment.status = "completed"
                payment.save()

                send_payment_confirmation_email.delay(payment.user.email, payment.amount, payment.booking_reference)
                return Response({"status": "Payment successful. Confirmation email sent."}, status=status.HTTP_200_OK)

            else:
                payment.status = "failed"
            payment.save()
            return Response({"status": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)