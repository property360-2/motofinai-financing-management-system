# Render Deployment Setup (DC Financing Corporation)

Use this checklist to deploy the Django app to Render with the provided Postgres database.

## 1) Environment Variables
Set these in Render **Environment**:
- `DJANGO_SECRET_KEY` = generate a strong value
- `DJANGO_DEBUG` = `false`
- `DJANGO_ALLOWED_HOSTS` = `your-service.onrender.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://your-service.onrender.com`
- `DB_ENGINE` = `django.db.backends.postgresql`
- `DB_NAME` = `dc_financing_corporation_financing`
- `DB_USER` = `dc_financing_corporation_financing_user`
- `DB_PASSWORD` = `5yxZnmEqEQOY4gzqKLi911zPGqcriHBL`
- `DB_HOST` = `dpg-d4jr1l4hg0os73a9sj70-a.oregon-postgres.render.com`
- `DB_PORT` = `5432`
- `DB_CONN_MAX_AGE` = `60`
- `DEFAULT_FROM_EMAIL` = `noreply@dcfinancingcorp.com`
- (optional) `DATABASE_URL` = `postgresql://dc_financing_corporation_financing_user:5yxZnmEqEQOY4gzqKLi911zPGqcriHBL@dpg-d4jr1l4hg0os73a9sj70-a.oregon-postgres.render.com/dc_financing_corporation_financing`

## 2) Build & Start Commands
- Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start: `gunicorn motofinai.wsgi:application --bind 0.0.0.0:$PORT`

## 3) Database Migration
- Run once after the service builds: `python manage.py migrate`

## 4) Create Admin User (optional)
- `python manage.py createsuperuser`

## 5) Local `.env` (already written)
Your local `.env` now points to the Render Postgres instance. Do **not** commit `.env`; it’s in `.gitignore`.

## Reference
- External DB URL: `postgresql://dc_financing_corporation_financing_user:5yxZnmEqEQOY4gzqKLi911zPGqcriHBL@dpg-d4jr1l4hg0os73a9sj70-a.oregon-postgres.render.com/dc_financing_corporation_financing`
- psql: `PGPASSWORD=5yxZnmEqEQOY4gzqKLi911zPGqcriHBL psql -h dpg-d4jr1l4hg0os73a9sj70-a.oregon-postgres.render.com -U dc_financing_corporation_financing_user dc_financing_corporation_financing`

> Note: Keep secrets out of tracked files. `.env` is ignored; use it locally and set env vars in Render.
