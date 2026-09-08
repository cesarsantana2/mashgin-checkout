# Mashgin Checkout

A small self-service checkout application for a snack bar, built as a take-home engineering exercise.

The application allows a customer to browse a menu, build an order, and complete a simulated checkout without cashier interaction.

## Tech Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- MySQL
- pytest
- Ruff

### Frontend

- Vue 3
- TypeScript
- Vite
- Pinia
- Vitest
- ESLint
- Nginx

### Infrastructure

- Docker
- Docker Compose

## Quick Start

The easiest way to run the complete application is with Docker Compose.

### Prerequisites

- Git
- Docker
- Docker Compose

### Operating Systems

The recommended Docker Compose setup is designed to work on:

- Linux with Docker Engine and Docker Compose — **tested**
- macOS with Docker Desktop — expected to work
- Windows with Docker Desktop — **validation in progress**

The main startup command is the same on all platforms:

```bash
docker compose up --build
```

The complete Dockerized flow has been validated on Linux. A Windows Docker Desktop smoke test is currently in progress.

Local development instructions below use Unix-style shell commands. On Windows, Docker Compose is the recommended way to run the complete application.

### Start the application

Clone the repository:

```bash
git clone git@github.com:cesarsantana2/mashgin-checkout.git
cd mashgin-checkout
```

Build and start the application:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8080
```

The services are exposed by default as:

| Service | Address |
| --- | --- |
| Frontend | `http://localhost:8080` |
| API | `http://localhost:8000` |
| API health check | `http://localhost:8000/health` |
| MySQL | `localhost:3307` |

The API container automatically runs database migrations and seeds the menu before starting FastAPI.

To run the stack in the background:

```bash
docker compose up -d
```

To stop it:

```bash
docker compose down
```

To completely reset the application, including the MySQL volume:

```bash
docker compose down -v
```

### Port conflicts

If port `8000` is already being used on the host, the API host port can be changed without changing the container configuration:

```bash
API_PORT=8001 docker compose up -d
```

The API will then be available directly at:

```text
http://localhost:8001
```

The frontend continues to communicate with the API through Nginx and Docker's internal network.

The frontend port can similarly be changed:

```bash
FRONTEND_PORT=8081 docker compose up -d
```

## Architecture

The project is intentionally implemented as a small modular monolith rather than a collection of microservices.

```text
Browser
   |
   v
Vue 3 + Pinia
   |
   | /api/v1/*
   v
Nginx
   |
   v
FastAPI
   |
   v
SQLAlchemy
   |
   v
MySQL
```

Docker Compose connects three services:

- `frontend` — builds the Vue application and serves it with Nginx.
- `api` — runs the FastAPI application.
- `db` — runs MySQL.

Nginx serves the compiled frontend and proxies `/api/*` requests to the API container.

This keeps the browser on a single origin in the containerized application and avoids exposing infrastructure details to the frontend.

## Project Structure

```text
mashgin-checkout/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   └── schemas/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── stores/
│   │   └── __tests__/
│   ├── Dockerfile
│   └── nginx.conf
├── compose.yaml
└── README.md
```

The backend separates HTTP concerns, validation schemas, persistence models, and database infrastructure while keeping the application small enough to navigate easily.

## API

### Health

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### Menu

```http
GET /api/v1/menu
```

Returns the menu.

Prices are represented as integer cents rather than floating-point numbers.

Example item:

```json
{
  "id": 1,
  "name": "Chips",
  "description": "Classic potato chips",
  "price_cents": 199,
  "available": true
}
```

### Create Order

```http
POST /api/v1/orders
Idempotency-Key: <unique-key>
```

Example request:

```json
{
  "items": [
    {
      "menu_item_id": 1,
      "quantity": 2
    }
  ],
  "payment": {
    "method": "card"
  }
}
```

The backend:

1. validates the request;
2. verifies that every menu item exists;
3. verifies that every requested item is available;
4. reads authoritative prices from the database;
5. calculates the total server-side;
6. persists the order and its items;
7. returns the completed order.

The frontend never determines the authoritative order total.

## Idempotency

Checkout requests require an `Idempotency-Key`.

This protects the customer from accidentally creating duplicate orders when, for example:

- the checkout button is clicked twice;
- the client retries after a timeout;
- the server successfully creates an order but the response is lost.

The idempotency key has a unique database constraint.

The API first checks whether an order with the same key already exists. It also handles a possible database race by catching a uniqueness conflict, rolling back the failed transaction, and returning the order created by the competing request.

The frontend reuses the same idempotency key when retrying the same order payload and creates a new key when the order changes.

For this take-home, reusing a key with a different payload returns the original order. In a production payment system, I would additionally persist a request fingerprint and reject reuse of the same key with a different payload.

## Data Model

The main domain entities are:

```text
MenuItem
Order
OrderItem
```

`OrderItem` stores a snapshot of the item's name and unit price at checkout time.

This is intentional: historical orders should not change if a menu item's name or price changes later.

Money is stored as integer cents (`price_cents`, `unit_price_cents`, and `total_cents`) to avoid floating-point rounding errors.

## Error Handling

The API handles cases including:

- empty orders;
- zero or negative quantities;
- nonexistent menu items;
- unavailable menu items;
- duplicate checkout requests.

The frontend provides explicit loading, success, and failure states.

If checkout fails because of a transient network problem, the customer can retry without creating a duplicate order.

## Payment

Payment is deliberately simulated.

The client sends:

```json
{
  "method": "card"
}
```

No card number, CVV, or other sensitive payment information is collected or persisted.

A production implementation would delegate payment details to a PCI-compliant payment provider and would store only safe provider identifiers and payment state.

## Database and Migrations

The application uses MySQL with SQLAlchemy.

Schema evolution is managed with Alembic rather than creating production tables dynamically from ORM metadata.

When Docker starts the API, Compose runs:

```bash
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The commands are chained with `&&`, so the API starts only if migrations and seeding succeed.

The seed operation is idempotent and does not recreate menu items that already exist.

### Database URL

For local backend development, the default database URL points to:

```text
mysql+pymysql://mashgin:mashgin@localhost:3307/mashgin_checkout
```

Inside Docker Compose, the API receives:

```text
mysql+pymysql://mashgin:mashgin@db:3306/mashgin_checkout
```

`db` is the Docker Compose service name. Docker's internal DNS resolves it to the MySQL container.

The distinction is important: `localhost` inside the API container refers to the API container itself, not the database container.

## Local Development

Docker Compose is the recommended way to run the complete application, but the backend and frontend can also be run independently during development.

### Backend

From `backend/`:

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
alembic upgrade head
```

Seed the menu:

```bash
python -m app.db.seed
```

Start FastAPI with automatic reload:

```bash
uvicorn app.main:app --reload
```

The API runs at:

```text
http://localhost:8000
```

### Frontend

From `frontend/`:

Install dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The development frontend runs at:

```text
http://localhost:5173
```

During local development, Vite proxies `/api` requests to the backend running on port `8000`.

## Testing and Quality

### Backend

From `backend/` with the virtual environment active:

Run all tests:

```bash
pytest
```

Verbose test output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_menu.py
```

Check Python lint issues:

```bash
ruff check .
```

Automatically fix safe lint issues:

```bash
ruff check . --fix
```

Format Python code:

```bash
ruff format .
```

Verify formatting without changing files:

```bash
ruff format --check .
```

### Frontend

From `frontend/`:

Install exactly the dependency versions from the lockfile:

```bash
npm ci
```

Run unit tests:

```bash
npm run test:unit -- --run
```

Run lint checks:

```bash
npm run lint
```

Run TypeScript checks:

```bash
npm run type-check
```

Create the production build:

```bash
npm run build
```

## Alembic Command Reference

Useful migration commands from `backend/`:

Show the currently applied migration:

```bash
alembic current
```

Show migration history:

```bash
alembic history
```

Apply all pending migrations:

```bash
alembic upgrade head
```

Generate a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe the change"
```

Generated migrations should always be reviewed before being applied.

## Docker Command Reference

Run these commands from the repository root.

Build and start the complete stack:

```bash
docker compose up --build
```

Start in the background:

```bash
docker compose up -d
```

Show project containers:

```bash
docker compose ps
```

Follow API logs:

```bash
docker compose logs -f api
```

Follow frontend logs:

```bash
docker compose logs -f frontend
```

Stop and remove containers:

```bash
docker compose down
```

Reset containers and the database volume:

```bash
docker compose down -v
```

Execute a command inside a running service:

```bash
docker compose exec <service> <command>
```

For example, inspect the active Nginx configuration:

```bash
docker compose exec frontend nginx -T
```

## Git Command Reference

Inspect the working tree:

```bash
git status
```

Compact status:

```bash
git status --short
```

Inspect unstaged changes:

```bash
git diff
```

Inspect staged changes:

```bash
git diff --staged
```

Stage selected files:

```bash
git add <files>
```

Create a commit:

```bash
git commit -m "description"
```

Push commits:

```bash
git push
```

## Design Decisions and Trade-offs

### Modular monolith over microservices

The application has a small domain and a single deployment unit.

Splitting menu and order functionality into separate services would add operational complexity without solving a current scaling or ownership problem.

The internal structure still keeps responsibilities separated so parts can evolve independently.

### Server-side pricing

The client sends product IDs and quantities, not trusted prices.

The API loads current prices from the database and calculates the total itself.

This prevents stale or manipulated client prices from becoming authoritative.

### Integer cents

Monetary values are represented as integers rather than floating-point numbers to avoid binary floating-point rounding problems.

For example:

```text
$1.99 → 199
$2.49 → 249
$4.48 → 448
```

### Price and name snapshots

Orders preserve the item name and price that existed when checkout occurred.

Historical transactions therefore remain stable even if the menu changes later.

### Database-backed idempotency

Idempotency is enforced by a unique database constraint rather than only application memory.

This remains effective across process restarts and multiple API workers.

### Nginx as the frontend entry point

The production frontend is compiled into static assets and served by Nginx.

Nginx also proxies `/api/*` to FastAPI through the Docker network.

The browser therefore interacts with one origin:

```text
Browser → Nginx → FastAPI
```

rather than needing to know where the backend container lives.

### No administration UI

The exercise focuses on the customer checkout experience.

An administration interface for creating or editing menu items was intentionally left out to keep the implementation focused.

### Simulated payment

The assignment does not require real payment processing.

Collecting fake card details would add security-sensitive UI without demonstrating useful payment integration, so the application models only the payment method.

## What I Would Add Next

Given more production scope, possible extensions would include:

- integration with a real payment provider;
- request fingerprints for stricter idempotency semantics;
- authentication and authorization for administrative operations;
- inventory management;
- menu administration;
- richer order lifecycle states;
- structured logging and metrics;
- end-to-end browser tests;
- production secrets management.

These were intentionally not added to keep the take-home focused on the core self-service checkout flow.

## AI-Assisted Development

AI tools were used during development as an engineering assistant for brainstorming, implementation support, debugging, test-case exploration, and documentation.

All generated or suggested changes were reviewed, executed, tested, and iterated on as part of the development process.

Examples of decisions that were explicitly evaluated rather than accepted mechanically include:

- choosing a modular monolith instead of microservices;
- representing money as integer cents;
- calculating totals on the server;
- preserving order-item snapshots;
- implementing database-backed idempotency;
- keeping payment simulated and avoiding sensitive card data;
- using Docker Compose to make the complete environment reproducible.

The final implementation and its trade-offs remain the responsibility of the author.