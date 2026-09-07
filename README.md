# Mehr übrig 🇦🇹

A German-language household budget planner built with **Django 5.2 + PostgreSQL**.
A responsive violet-and-charcoal interface, clear income/spending summaries,
a live allocation chart and a savings scenario help users understand their month.

## Features

- Registration with email, login/logout, password change, and email password reset.
- Database-backed login protection: five failures lock a username for 15 minutes.
- One private budget per user per calendar month, editable after saving.
- Income and seven expense categories, with server-side validation.
- Cents-based live calculations, deficit states, and hypothetical savings.
- The input/save flow also works without JavaScript.
- Confirmation before replacing inputs or leaving with unsaved changes.
- CSV download of saved budgets and a confirmation page for deleting a month.
- Responsive layouts, keyboard focus states, labeled fields, accessible errors,
  password visibility controls and reduced-motion support.
- No external fonts, scripts, analytics, bank connections, or fabricated market data.

## Start locally with Docker

```sh
git clone https://github.com/Mario8802/mehr-uebrig.git
cd mehr-uebrig
cp .env.example .env
```

PowerShell: use `Copy-Item .env.example .env` instead of `cp`.
Generate a secret and a database password:

```sh
python -c "import secrets; print(secrets.token_urlsafe(64)); print(secrets.token_urlsafe(32))"
```

Put the first value in `DJANGO_SECRET_KEY`, the second in `POSTGRES_PASSWORD`.
Keep `DJANGO_DEBUG=1` for local HTTP development, then:

```sh
docker compose up --build
```

Open **http://localhost:8000**. Create an account or try the example budget.
Migrations and static collection run before Gunicorn. The database uses a named
volume and is not exposed on a host port. The app binds to localhost only.

```sh
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
docker compose down
```

`down` retains the database; `down -v` erases it. Never commit `.env`.

## Local Python setup

Use Python 3.12 and PostgreSQL 14+ (17 is used in Docker and CI).
Create a PostgreSQL database and role, then:

```sh
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Copy and fill `.env.example` as `.env`; settings load it without overriding
already-exported environment variables. Configure `POSTGRES_*` or `DATABASE_URL`.

```sh
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

## Deploy

**[Инструкции на български за Render и PythonAnywhere →](docs/DEPLOYMENT.md)**

`render.yaml` defines a production-oriented paid web service and PostgreSQL 17
in Frankfurt. Applying it in Render can incur charges; review the plan first.
`build.sh` installs dependencies and collects static files, pre-deploy runs
migrations, and `/health/` checks database connectivity. The app has not been
deployed to a hosting account by this change.

PythonAnywhere needs a compatible PostgreSQL version, not just PostgreSQL access.
Confirm **14+** before choosing its built-in database; the deployment guide covers
this and includes a WSGI example.

Production password reset requires SMTP settings and a verified sender. Without
those, the reset route returns a clear unavailable message. In local debug mode,
reset emails are printed to the console. New signups collect email; existing
accounts without email need their address updated through the admin first.

Before inviting users, configure real operator/privacy pages, SMTP, backups and
proxy-level throttling for registration and reset requests. Email verification
and self-service account deletion are not included in this release.

## Tests

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
python manage.py test
node --test tests/calculator.test.cjs
```

The 21 Django tests cover ownership, monthly updates, no-JavaScript forms, input
validation, CSRF, password reset token flow, login lockouts, CSV/delete permissions,
HTTPS behavior and health checks. Four Node tests cover money arithmetic and
rounding. GitHub Actions runs Django tests against PostgreSQL 17 and can also be
started with **Run workflow**.

Local verification used a temporary SQLite test configuration outside the repo;
all 21 Django and four Node tests passed. PostgreSQL integration, Docker startup,
real SMTP delivery and browser/visual testing have not been executed in this
workspace. Passing application tests is not a substitute for the hosting smoke
test described in the deployment guide.

`check --deploy` can report advisory HSTS subdomain/preload warnings: these are
intentionally not enabled without knowing the eventual domain's HTTPS policy.
The Axes username-only configuration suppresses its IP-policy advisory, with a
specific regression test proving that rotating cookies/user agents does not bypass
the same-username limit. Configure signup/reset throttling at the real proxy/WAF.

## Money assumptions

Enter regular monthly net income without 13th/14th salary. Empty amounts are zero;
negative amounts and values above €1,000,000 per field are rejected. Daily money is
a simple 30-day equivalent. The savings slider models reductions in food, mobility,
phone/internet and other spending. It provides arithmetic, not guaranteed savings,
financial advice, tax calculations or verified offers. Monthly savings round half
up to cents; annual savings are twelve times that rounded monthly amount.

Guest entries are not copied into a newly created account. Unsaved changes prompt
before navigation when JavaScript is available. CSV exports reflect saved data.
