# EventHub

EventHub is a Django REST Framework API for browsing events, reserving seats,
and cancelling reservations.

## Run with Docker (recommended)

```bash
docker compose up --build
```

Compose starts the Django API and PostgreSQL database, waits for PostgreSQL to
be healthy, and applies migrations before starting the web server. The API is
available at `http://127.0.0.1:8000/api/`. Visiting
`http://127.0.0.1:8000/` redirects to the events list. PostgreSQL data persists
in a Docker volume when the containers are stopped.

For a database client running on your computer, connect to host `localhost`,
port `5434`, database `eventhub`, user `eventhub`, and the configured
`POSTGRES_PASSWORD` (the local default is `eventhub-dev-password`). The port is
bound to localhost only and differs from `5432` to avoid conflicts with other
local PostgreSQL containers. From the Django container, the database host and
port remain `db:5432`.

Stop the containers with `Ctrl+C` or `docker compose down`. To also remove the
database volume and its data, run `docker compose down -v`.

Compose uses development-only defaults for local use. To customize them, create
a `.env` file in the project root with values such as:

```dotenv
POSTGRES_DB=eventhub
POSTGRES_USER=eventhub
POSTGRES_PASSWORD=replace-with-a-local-password
DJANGO_SECRET_KEY=replace-with-a-local-secret
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Do not use the development defaults or `DEBUG=true` in a production deployment.

## Run locally (without Docker)

With the Compose database running, the local Django process defaults to
`localhost:5434` with the development credentials above. If you use a different
database or credentials, configure `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` in your environment.
Then run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

If your shell already defines `POSTGRES_PORT` as `5432`, override it with
`export POSTGRES_PORT=5434` before starting Django locally. The Compose app
container uses `db:5432` instead.

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
