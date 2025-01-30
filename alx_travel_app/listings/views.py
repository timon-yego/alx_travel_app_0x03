from django.shortcuts import render
from rest_framework import viewsets
from .models import Listing, Booking, Review
from .serializers import ListingSerializer, BookingSerializer, ReviewSerializer
from .tasks import send_booking_confirmation

# Create your views here.
class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        # Save the booking first
        booking = serializer.save()
        # Trigger email task asynchronously
        send_booking_confirmation.delay(booking.id)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
