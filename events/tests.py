from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Event, Reservation


class EventHubApiTests(APITestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="Community Conference",
            venue="Central Hall",
            date=date.today() + timedelta(days=30),
            total_seats=5,
            available_seats=5,
        )

    def test_root_redirects_to_events_api(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response["Location"], "/api/events/")

    def test_create_and_filter_events(self):
        create_response = self.client.post(
            reverse("event-list"),
            {
                "title": "Developer Meetup",
                "venue": "North Campus",
                "date": str(date.today() + timedelta(days=60)),
                "total_seats": 20,
                "available_seats": 20,
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["reservations_count"], 0)

        response = self.client.get(
            reverse("event-list"),
            {"status": "upcoming", "venue": "central"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.event.id)

    def test_event_rejects_available_seats_above_total(self):
        response = self.client.post(
            reverse("event-list"),
            {
                "title": "Invalid Event",
                "venue": "Central Hall",
                "date": str(date.today() + timedelta(days=5)),
                "total_seats": 2,
                "available_seats": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("available_seats cannot exceed total_seats.", str(response.data))

    def test_reservation_deducts_seats_and_overbooking_is_rejected(self):
        reservation_url = reverse("reservation-list")
        payload = {
            "event": self.event.id,
            "attendee_name": "Priya Sharma",
            "attendee_email": "priya@example.com",
            "seats_reserved": 4,
        }

        created = self.client.post(reservation_url, payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 1)
        self.assertEqual(created.data["status"], "confirmed")

        payload["seats_reserved"] = 2
        rejected = self.client.post(reservation_url, payload, format="json")
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only 1 seat(s) available.", str(rejected.data))
        self.assertEqual(Reservation.objects.count(), 1)

    def test_cancellation_restores_seats_and_cannot_be_repeated(self):
        reservation = Reservation.objects.create(
            event=self.event,
            attendee_name="Priya Sharma",
            attendee_email="priya@example.com",
            seats_reserved=2,
        )
        Event.objects.filter(pk=self.event.pk).update(available_seats=3)

        response = self.client.post(
            reverse("reservation-cancel", args=[reservation.pk]),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 5)

        repeated = self.client.post(
            reverse("reservation-cancel", args=[reservation.pk]),
            format="json",
        )
        self.assertEqual(repeated.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(repeated.data["error"], "Already cancelled.")
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 5)

    def test_reservations_can_be_filtered_by_event(self):
        reservation = Reservation.objects.create(
            event=self.event,
            attendee_name="Priya Sharma",
            attendee_email="priya@example.com",
            seats_reserved=1,
        )

        response = self.client.get(
            reverse("reservation-list"),
            {"event_id": self.event.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [reservation.id])
