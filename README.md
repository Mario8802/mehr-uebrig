# Mehr übrig 🇦🇹

A Django + PostgreSQL household budget planner for Austria. German interface, monthly budgets, user accounts, and an interactive savings scenario.

## What works

- Try the calculator before creating an account.
- Register, log in, and save one budget per calendar month.
- Enter net income and seven expense categories.
- See total spending, remaining money, and a 30-day daily equivalent.
- Model a 0–50% reduction in food, mobility, phone/internet, and miscellaneous spending.
- Reopen and update saved months. Each user can access only their own budgets.

Savings are hypothetical arithmetic based on the user's figures, not verified offers or guaranteed reductions. Regular monthly net income excludes 13th/14th salary. Empty fields count as zero when submitted from the interface. Preview figures are not carried across registration. There is no bank connection, tax calculation, tariff feed, or automatic benefit eligibility check.

## Stack

Python 3.12, Django 5.2 LTS, PostgreSQL 17, psycopg 3, Gunicorn, WhiteNoise, server-rendered templates and vanilla JavaScript. No Node build is required. No external fonts, analytics, or JavaScript CDNs are loaded.

## Run on Windows, macOS, or Linux with Docker

Install Docker with Compose, then in the project directory:

```sh
cp .env.example .env
```

PowerShell equivalent:

```powershell
Copy-Item .env.example .env
```

Generate two independent random values:

```sh
python -c "import secrets; print(secrets.token_urlsafe(64)); print(secrets.token_urlsafe(32))"
```

Put the first in `DJANGO_SECRET_KEY` and the second in `POSTGRES_PASSWORD` in `.env`. Keep `DJANGO_DEBUG=1` for local HTTP development. Never commit `.env`.

```sh
docker compose up --build
```

Open http://localhost:8000, create an account, and save a budget. Migrations and static-file collection run automatically before the web server starts. PostgreSQL data lives in a named Docker volume. The database is not published to the host network; the web server binds to localhost only.

```sh
docker compose exec web python manage.py test
docker compose exec web python manage.py createsuperuser
docker compose down
```

`docker compose down` preserves database data. Do not use `down -v` unless you intend to erase the database volume.

## Run without Docker

Install Python 3.12 and PostgreSQL 17. Create a database and non-superuser application role; use separate credentials for testing if your application role cannot create test databases. Create a virtual environment and install dependencies:

```sh
python -m venv .venv
# PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Export the variables from `.env.example` into the process environment (Django does not load `.env` automatically outside Docker). Set `POSTGRES_HOST` to your database host. Then:

```sh
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

## Tests and CI

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The GitHub Actions workflow uses a real PostgreSQL 17 service. Tests cover decimal arithmetic, invalid input, uniqueness and bounds constraints, account isolation, CSRF, monthly updates, registration, login/logout, and cache protection. CI needs a database role allowed to create a test database. A workflow being included does not mean it has already run on GitHub.

## Deployment

This is a standard Python/Django service and needs a host that runs Python plus PostgreSQL. GitHub stores code and runs CI; GitHub Pages cannot run this application. The provided Compose file is for local development, not a public HTTPS deployment.

For a public deployment:

- Use a fresh secret and database credentials; set `DJANGO_DEBUG=0`.
- Set exact `DJANGO_ALLOWED_HOSTS` and HTTPS `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Terminate HTTPS at a trusted reverse proxy. Only set `DJANGO_TRUST_PROXY=1` if that proxy strips and replaces the incoming forwarded-protocol header.
- Use the database provider's TLS requirements (`POSTGRES_SSLMODE=require` or its stronger verified configuration).
- Run migrations and `collectstatic`, then the Gunicorn command from the Dockerfile.
- Run `python manage.py check --deploy` in the actual deployment configuration.
- Set up database backups, access logging policies, monitoring, authentication rate limiting at the proxy, and applicable privacy/legal pages before opening registration to the public.

Users' budget rows belong to their authenticated account; staff with database/admin access can still administer the service. Passwords use Django's password hashing. Django CSRF, secure production cookies, HTTPS redirect and HSTS are enabled. Public email verification and self-service password reset are not implemented in this first version.

## Layout

```text
config/        Django settings, routes and WSGI
budget/        Models, forms, views, migrations and tests
templates/     Dashboard and account pages
static/        Responsive CSS and calculator JavaScript
.github/       PostgreSQL-backed CI
```

Official framework reference: https://docs.djangoproject.com/en/5.2/

## Verification for this delivery

Django system checks, template rendering through the test client, static-file collection, JavaScript syntax and 11 application tests passed locally. The application tests used a temporary SQLite test configuration outside the repository because this environment had no PostgreSQL server. PostgreSQL runtime integration and Docker startup have **not** been executed here. Production settings use PostgreSQL only; the GitHub Actions workflow runs the same tests against PostgreSQL 17 once pushed. No browser interaction or visual testing was performed.
