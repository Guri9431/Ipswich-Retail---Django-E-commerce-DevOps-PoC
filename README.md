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
Stop with `docker compose down` (add `-v` to wipe the SQLite volume).

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

## CI/CD pipeline (`.github/workflows/ci-cd.yml`)

`push / pull request` -> **lint (flake8)** -> **Django check + migration check** -> **tests + coverage gate (80%)** ->
**Docker build + container smoke test** -> **deploy to Render (main only, via deploy hook)** -> **post-deploy health check** ->
**Slack notification**.

### GitHub repository secrets to add
| Secret | Purpose |
|---|---|
| `RENDER_DEPLOY_HOOK_URL` | Render service -> Settings -> Deploy Hook |
| `LIVE_URL` | e.g. `https://ipswich-retail.onrender.com` (for the post-deploy check) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook (optional) |

Steps whose secret is missing skip cleanly, so the pipeline is green before you wire up Render and Slack.

## Deploying free on Render

1. Push this repo to a **public** GitHub repository.
2. Render dashboard -> **New** -> **Blueprint** -> select the repo (`render.yaml` is picked up), free plan.
3. Copy the service's **Deploy Hook** URL into the `RENDER_DEPLOY_HOOK_URL` GitHub secret; set `LIVE_URL`.
4. Push to `main` and the pipeline deploys it. Put the live URL and demo credentials in your report.

Limitation to mention in the report: Render's free tier has an ephemeral disk and spins down when idle, so the SQLite
database is recreated and re-seeded after each deploy or restart. Production would use managed PostgreSQL.

## Branching strategy

`main` (production, protected) <- `develop` (integration) <- `feature/*` branches via pull requests. CI runs on every PR;
only merges to `main` deploy.

## Project layout

```
config/                Django project (settings, urls, wsgi)
store/                 App: models, views, forms, cart.py, templates/, static/, tests.py, management/commands/seed_data.py
monitoring/            Prometheus config + alert rules, Grafana provisioning and dashboard JSON
.github/workflows/     CI/CD pipeline
Dockerfile, entrypoint.sh, docker-compose.yml, render.yaml
docs/                  Architecture, wireframes (draw.io-ready) and report-support notes
```

## Product images - adding your own

Each product shows, in this order: **your local file** -> the product's **Image url** (admin; defaults to an online photo)
-> a generated SVG -> `placeholder.svg`. A broken online photo therefore falls back automatically.

**To use your own picture for a product:**
1. Save it in `store/static/store/products/` named exactly `<product-slug>.jpg` (`.jpeg`, `.png`, `.webp`, `.avif` also work),
   e.g. `bamboo-chopping-board.jpg`.
2. VS Code: refresh the browser. Docker: `docker compose up --build`.

No code or database change needed. Run `python manage.py image_status` to list every product, its exact filename and the
source currently in use. For a hosted photo instead, set the product's **Image url** in `/admin/`.
New products: add the picture as `<slug>.jpg`, where the slug is the product's slug in the admin.
