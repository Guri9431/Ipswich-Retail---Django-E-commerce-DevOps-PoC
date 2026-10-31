# Ipswich Retail - Django E-commerce DevOps PoC

Proof-of-concept replacement for Ipswich Retail's monolithic shop, built with **Django (Model-View-Template)**,
**SQLite**, **Docker**, a **GitHub Actions CI/CD pipeline**, and **Prometheus + Grafana** monitoring.

University of Suffolk, MSc Computer Science, DevOps case study.

## Pages (4 customer pages + admin)

| Page | URL |
|---|---|
| Catalogue (search, categories, pagination) | `/` , `/category/<slug>/` |
| Product detail | `/product/<slug>/` |
| Basket | `/cart/` |
| Checkout and order confirmation | `/checkout/`, `/order/<id>/confirmation/` |
| Order history, login, register | `/orders/`, `/login/`, `/register/` |
| Admin | `/admin/` |
| Health probe / Prometheus metrics | `/health/`, `/metrics` |

## Demo accounts (created by `seed_data`)

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@12345` |
| Customer | `customer` | `Customer@12345` |

Override with `DEMO_ADMIN_PASSWORD` / `DEMO_CUSTOMER_PASSWORD` for any real deployment.

## Option A - run in VS Code (no Docker)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```
Open http://127.0.0.1:8000. Use the **Run and Debug** panel ("Django: runserver") or `Ctrl+Shift+B`.

## Option B - run in Docker Desktop (full stack with monitoring)

```bash
docker compose up --build
```

| Service | URL | Login |
|---|---|---|
| Shop | http://localhost:8000 | see demo accounts |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | `admin` / `admin` (dashboard "Ipswich Retail - Application Health" is pre-provisioned) |

Generate some traffic (browse, add to basket, checkout) and watch the Grafana panels update.
Stop with `docker compose down` (add `-v` to wipe the PostgreSQL volume).

Run only the app container:
```bash
docker build -t ipswich-retail .
docker run -p 8000:8000 -v ipswich_data:/data ipswich-retail
```

## Tests

```bash
python manage.py test                      # 23 tests: unit, integration, end-to-end
coverage run --source=store manage.py test && coverage report
flake8 .
```

| Level | Where | What it covers |
|---|---|---|
| Unit | `ModelUnitTests`, `CartUnitTests` | models, cart logic, stock caps |
| Integration | `CatalogueIntegrationTests` | views + templates + DB, validation, auth, `/health/`, `/metrics` |
| End-to-end | `EndToEndJourneyTests` | register -> browse -> basket -> checkout -> stock update -> order history; stock race |
| Pipeline smoke | `.github/workflows/ci-cd.yml` | builds the Docker image, starts it, curls `/health/`, `/`, `/cart/`, `/metrics` |


## Project layout

```
config/                Django project (settings, urls, wsgi)
store/                 App: models, views, forms, cart.py, templates/, static/, tests.py, management/commands/seed_data.py
monitoring/            Prometheus config + alert rules, Grafana provisioning and dashboard JSON
.github/workflows/     CI/CD pipeline
Dockerfile, entrypoint.sh, docker-compose.yml, render.yaml
docs/                  Architecture, wireframes (draw.io-ready) and report-support notes
```
