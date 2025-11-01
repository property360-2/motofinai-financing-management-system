# Repository Guidelines

## Project Structure & Module Organization
The Django project lives under `motofinai/`, with per-domain apps in `motofinai/apps/` (`loans`, `payments`, `inventory`, `risk`, `audit`, `archive`, etc.). Templating follows Atomic Design in `motofinai/templates/` (`components/atoms|molecules|organisms` plus `layouts/` and `pages/`). Static assets reside in `motofinai/static/`, while uploaded media is routed to the configured object store via `motofinai/media/`. Planning references and schema notes are in `documentation/`; update those when implementation diverges.

## Build, Test, and Development Commands
Create a virtual environment and install dependencies:
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```
Apply schema changes and run the server:
```bash
python manage.py migrate
python manage.py runserver
```
Execute the unit test suite (defaults to SQLite in-memory):
```bash
python manage.py test
```
Use `python manage.py createsuperuser` for initial admin access and `python manage.py collectstatic` before packaging for deployment.

## Coding Style & Naming Conventions
Write Python 3.11+ with Black-formatted, 4-space indentation (`black .`). Enforce imports ordering through `isort`. Module names stay snake_case; Django models are `CamelCase`, fields are snake_case, and HTML/CSS classes follow BEM where practical. Keep templates modular—atoms never reach template context directly; compose them through molecules/organisms.

## Testing Guidelines
Store app-specific tests in `<app>/tests/` with files named `test_<feature>.py`. Cover business rules called out in `documentation/plan.md`—loan schedules, risk scoring, audit logging, archive restore, and permission checks. When models touch the archive, add regression fixtures guarding JSON snapshots. Aim for ≥80% coverage on core apps using `coverage run python manage.py test` and report via `coverage html`.

## Commit & Pull Request Guidelines
Recent commit history is informal (`"Phase 3 Complete"`, `"im not stupid..."`). Move toward Conventional Commits (`feat: loans schedule recalculation`) in the imperative mood. Reference issue IDs in the body when applicable. Pull requests should include: concise summary, linked issue/task, migration notes, test evidence (`python manage.py test` output), and screenshots or GIFs for UI tweaks. Flag secrets in config diffs and remind reviewers to rotate environment keys if leaked.

## Environment & Security Tips
Keep secrets in `.env` using the keys listed in `documentation/plan.md`. Never commit `.env` or CDN credentials. Verify S3-compatible storage endpoints locally with `python manage.py check --deploy` before enabling uploads, and restrict admin access via Django’s built-in IP allowlisting where possible.
