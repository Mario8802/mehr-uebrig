# Пускане в Render / PythonAnywhere

## Render — основният подготвен вариант

В корена има `render.yaml`: Python web service + PostgreSQL 17 във Frankfurt.
Избрани са платени `0.5c-512mb` и `0.1c-256mb` планове. Провери актуалната цена
в Render преди създаване. Тук не са създавани платени услуги.

1. В Render отвори **New → Blueprint** и избери `Mario8802/mehr-uebrig`.
2. Прегледай двата ресурса и цените, после приложи Blueprint.
3. Render генерира секретен ключ и свързва вътрешния `DATABASE_URL`.
   Неговият `RENDER_EXTERNAL_HOSTNAME` автоматично се добавя към Django hosts
   и CSRF trusted origins.
4. Build инсталира зависимостите, събира static файловете и пуска Django
   deployment checks. Pre-deploy прилага миграциите. Gunicorn стартира сайта.
5. Провери `/health/`. При проблем с базата отговаря с 503, без да показва
   технически подробности или пароли.
6. В Render Shell: `python manage.py createsuperuser`.
7. Настрой SMTP полетата по-долу. Изпрати тест за възстановяване на парола до
   собствен адрес и провери целия процес. Без SMTP страницата показва ясно,
   че услугата още не е достъпна; не твърди, че е изпратила писмо.

Автоматичните deploy-и са настроени да чакат успешни GitHub checks.
Провери първия GitHub Actions run. При липса на автоматичен run използвай
**Actions → Django + PostgreSQL → Run workflow** преди ръчен deploy.

### SMTP настройки

```text
EMAIL_HOST=<SMTP сървър>
EMAIL_PORT=587
EMAIL_HOST_USER=<потребител>
EMAIL_HOST_PASSWORD=<тайна>
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
DEFAULT_FROM_EMAIL=Mehr übrig <потвърден-адрес@твоя-домейн>
```

За SMTP с implicit TLS на порт 465: `EMAIL_USE_TLS=0`, `EMAIL_USE_SSL=1`.
Не включвай едновременно двата TLS режима. Избери SMTP доставчик и план,
които позволяват изходящи връзки от хостинга.

За собствен домейн добави точното име към `DJANGO_ALLOWED_HOSTS` и
`https://...` към `DJANGO_CSRF_TRUSTED_ORIGINS` (списъци, разделени със запетаи).
Никога не използвай `*` като удобен обход на host проверката.

## PythonAnywhere — провери PostgreSQL версията първо

Django 5.2 изисква **PostgreSQL 14+**. Поддръжката на PythonAnywhere е посочвала
PostgreSQL 12 за вградената услуга в публикация от октомври 2025.
Това не доказва текущата версия в твоя акаунт: провери я с `SELECT version();`
или попитай поддръжката **преди плащане**. Вграденият PostgreSQL е платена опция.
Ако още е 12, този проект няма да работи с нея. Използвай Render или съвместима
външна PostgreSQL база, до която твоят платен PythonAnywhere акаунт има достъп.
Не понижавай Django до неподдържана версия заради стара база.

При наличен PostgreSQL 14+ и Python 3.12:

```bash
git clone https://github.com/Mario8802/mehr-uebrig.git
cd mehr-uebrig
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Попълни `.env`: нов случаен ключ, `DJANGO_DEBUG=0`, точния host,
HTTPS CSRF origin, PostgreSQL параметри/URL и SMTP.
Настрой TLS според доставчика на базата. За Django зад доверения HTTPS proxy
на хостинга използвай `DJANGO_TRUST_PROXY=1` след проверка на неговата конфигурация.

В **Web → Add a new web app → Manual configuration** избери същия Python и
посочи virtualenv `/home/<username>/mehr-uebrig/.venv`. В WSGI файла от Web таба
копирай `deploy/pythonanywhere_wsgi.py`. Той зарежда `.env` преди Django.

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy --fail-level ERROR
python manage.py createsuperuser
```

Добави static mapping `/static/` → `/home/<username>/mehr-uebrig/staticfiles/`.
Натисни Reload. На PythonAnywhere не стартираш Gunicorn от Render командата —
уеб приложението се обслужва от техния WSGI механизъм.

## Преди да поканиш реални потребители

- Провери на реалния HTTPS адрес: регистрация, вход, запазване и смяна на месец,
  CSV, изтриване с отказ/потвърждение, logout и reset email.
- Конфигурирай backup на PostgreSQL и изпробвай възстановяване в отделна база.
- Добави операторски данни и приложимите правни/поверителни страници за твоята
  реална услуга. В проекта не са измислени фирма, адрес или правни уверения.
- За публична регистрация настрой ограничения при proxy/WAF за signup и
  password-reset endpoints, според истинската proxy/IP конфигурация.
  Включената Axes защита покрива login по потребителско име, не signup/reset.
- Не пази чувствителни production данни в screenshots, Git или CI logs.
- Периодично чисти старите сесии: `python manage.py clearsessions`.
  За старите login attempts: `python manage.py axes_reset_logs 30` (дни).
- Възстановяване на парола за стари акаунти без email изисква първо операторът
  да добави проверен адрес през Django admin.

## Източници

- [Render: Django](https://render.com/docs/deploy-django)
- [Render: pre-deploy commands](https://render.com/docs/deploys)
- [Render: Blueprint reference](https://render.com/docs/blueprint-spec)
- [PythonAnywhere: Django](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)
- [PythonAnywhere: PostgreSQL](https://help.pythonanywhere.com/pages/Postgres/)
- [PythonAnywhere: информация за версията от поддръжката](https://eu.pythonanywhere.com/forums/topic/558/)
- [Django 5.2: PostgreSQL 14+](https://docs.djangoproject.com/en/5.2/releases/5.2/)
