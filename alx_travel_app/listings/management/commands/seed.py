from django.core.management.base import BaseCommand
from listings.models import Listing, Booking, Review
import random

class Command(BaseCommand):
    help = "Seed the database with sample data"

    def handle(self, *args, **kwargs):
        # Clear existing data
        Listing.objects.all().delete()
        Booking.objects.all().delete()
        Review.objects.all().delete()

        # Create sample listings
        for i in range(10):
            listing = Listing.objects.create(
                title=f"Listing {i+1}",
                description="A wonderful place to stay.",
                price_per_night=random.uniform(50, 500),
                max_guests=random.randint(1, 10)
            )

            # Create sample bookings for each listing
            for j in range(random.randint(1, 5)):
                Booking.objects.create(
                    listing=listing,
                    guest_name=f"Guest {j+1}",
                    check_in="2024-12-01",
                    check_out="2024-12-05"
                )

            # Create sample reviews for each listing
            for k in range(random.randint(1, 3)):
                Review.objects.create(
                    listing=listing,
                    reviewer_name=f"Reviewer {k+1}",
                    rating=random.randint(1, 5),
                    comment="Great place!"
                )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
