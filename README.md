# EventHub

EventHub is a Django REST Framework API for browsing events, reserving seats,
and cancelling reservations.

## Setup and run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/`. Visiting
`http://127.0.0.1:8000/` redirects to the events list. The SQLite database is
created as `db.sqlite3` in the project root.

Run the automated API tests with:

```bash
python manage.py test events
```

## Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/events/` | List events. Supports `?status=upcoming` and `?venue=central` filters. |
| `POST` | `/api/events/` | Create an event. `available_seats` cannot exceed `total_seats`. |
| `GET` | `/api/events/{id}/` | Retrieve one event, including its confirmed reservation count. |
| `PUT` / `PATCH` | `/api/events/{id}/` | Update an event. |
| `DELETE` | `/api/events/{id}/` | Delete an event and its reservations. |
| `GET` | `/api/reservations/` | List reservations. Supports `?event_id={id}`. |
| `POST` | `/api/reservations/` | Reserve one or more seats for an upcoming or ongoing event. |
| `GET` | `/api/reservations/{id}/` | Retrieve one reservation. |
| `PUT` / `PATCH` | `/api/reservations/{id}/` | Update attendee details. Event and seat count are fixed after reservation so availability remains consistent. |
| `DELETE` | `/api/reservations/{id}/` | Delete a reservation. |
| `POST` | `/api/reservations/{id}/cancel/` | Cancel a confirmed reservation and restore its seats. |

Reservation creation accepts `event`, `attendee_name`, `attendee_email`, and
`seats_reserved`. For example:

```json
{
  "event": 1,
  "attendee_name": "Priya Sharma",
  "attendee_email": "priya@example.com",
  "seats_reserved": 2
}
```

To capture the requested Postman evidence, run the server and save a screenshot
of a successful `POST /api/reservations/` (`201 Created`), an overbooking
attempt (`400 Bad Request`), and `POST /api/reservations/{id}/cancel/` returning
the cancelled reservation.

## Design decision

Seat deduction and reservation creation run inside one database transaction.
The seat decrement is also a conditional database update (`available_seats`
must still be at least the requested amount), so concurrent requests cannot
reserve the same remaining seats. Cancellation only changes a confirmed
reservation once and restores its seats in the same transaction.
