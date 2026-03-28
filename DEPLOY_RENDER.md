# Deploy On Render

## What Was Changed

- `hospitalms/settings.py`
  - Supports `DATABASE_URL` for Render PostgreSQL
  - Keeps local MySQL support through environment variables
  - Adds production static file support with WhiteNoise
  - Adds secure proxy / HTTPS settings for Render
  - Adds optional Cloudinary media storage with `CLOUDINARY_URL`
- `core/__init__.py`
  - Uses `PyMySQL` when MySQL is needed locally
- `requirements.txt`
  - Adds `gunicorn`, `whitenoise`, `dj-database-url`, `psycopg[binary]`, `PyMySQL`, `cloudinary`, and `django-cloudinary-storage`
- `build.sh`
  - Runs `collectstatic` and `migrate` during Render build
- `render.yaml`
  - Blueprint for the web service and PostgreSQL database
- `.env.example`
  - Example environment variables for local and production use

## Recommended Render Setup

1. Push this project to GitHub.
2. In Render, create a new Blueprint and connect the repository.
3. Render will read `render.yaml` and create:
   - one Python web service
   - one PostgreSQL database
4. After first deploy, open the Render service settings and add:
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`
   - any custom `DJANGO_ALLOWED_HOSTS` values if needed
   - any custom `DJANGO_CSRF_TRUSTED_ORIGINS` values if needed
   - optional `CLOUDINARY_URL` if you want permanent media uploads

## Important Notes

- Render uses an ephemeral filesystem.
- Files uploaded to `/media/` are not permanent on Render.
- Your current app uploads reports and payment proof files.
- If you set `CLOUDINARY_URL`, the app will automatically store uploaded media in Cloudinary instead of local disk.
- If you do not use Cloudinary, local `/media/` on Render is temporary.

## Local Development

Local MySQL still works with:

- `DB_ENGINE=mysql`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

You can also use local SQLite with:

- `DB_ENGINE=sqlite`
