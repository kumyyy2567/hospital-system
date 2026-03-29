# Hospital Management System (Django + MySQL / Render Ready)

## Features
- Role-based authentication (Admin, Doctor, Patient)
- Patient records and history
- Doctor availability and appointment booking
- Email notifications via Gmail SMTP
- Prescription and invoice PDF generation
- Admin analytics dashboard with Chart.js
- Staff management, notifications, file uploads

## Local Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` values into your local environment.

3. Create a MySQL database:
   ```sql
   CREATE DATABASE hospital_db;
   ```

4. Configure environment variables (PowerShell):
   ```powershell
   $env:DB_ENGINE='mysql'
   $env:DB_NAME='hospital_db'
   $env:DB_USER='root'
   $env:DB_PASSWORD='your_mysql_password'
   $env:DB_HOST='127.0.0.1'
   $env:DB_PORT='3306'
   $env:EMAIL_HOST_USER='your_gmail@gmail.com'
   $env:EMAIL_HOST_PASSWORD='your_app_password'
   $env:DJANGO_SECRET_KEY='change-me'
   $env:DJANGO_DEBUG='True'
   ```

5. Run migrations and create superuser:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```
   The superuser is automatically treated as the owner admin.

6. Start the server:
   ```bash
   python manage.py runserver
   ```

## Render Deployment

This project is prepared for Render with:
- `render.yaml`
- `build.sh`
- `runtime.txt`
- production-ready Django settings

### Steps
1. Push the project to GitHub.
2. In Render, click `New +` -> `Blueprint`.
3. Connect the repository.
4. Render will create:
   - one web service
   - one PostgreSQL database
5. Add environment variables in Render:
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`
   - optional `CLOUDINARY_URL` if you want permanent media storage

### Important Production Note
- Render disk is ephemeral.
- Uploaded files like reports and payment proofs will not be permanent unless you use cloud media storage.
- This project now supports optional Cloudinary media storage through `CLOUDINARY_URL`.

## Railway Deployment

This project can also run on Railway with a Railway MySQL service.

### Steps
1. Create a new Railway project.
2. Add a MySQL service in Railway.
3. Add your Django app service from GitHub.
4. In the app service variables, set:
   - `DJANGO_SECRET_KEY`
   - `DJANGO_DEBUG=False`
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`
5. For database connection, set either:
   - `DATABASE_URL=${{MySQL.MYSQL_URL}}`
   - or `MYSQL_URL=${{MySQL.MYSQL_URL}}`

The app now supports both `DATABASE_URL` and Railway-style `MYSQL_URL`.

### Railway Note
- Railway internal MySQL hosts like `*.railway.internal` work from Railway services.
- They do not work directly from your local laptop.
- Local development should use local SQLite or local MySQL instead.

## Gmail SMTP Notes
- Enable 2-Step Verification on Gmail account.
- Create an App Password and use it as `EMAIL_HOST_PASSWORD`.

## Optional Cloudinary Media Storage

If you want persistent uploads in production:

```powershell
$env:CLOUDINARY_URL='cloudinary://API_KEY:API_SECRET@CLOUD_NAME'
```

Once `CLOUDINARY_URL` is set and dependencies are installed, uploaded media will use Cloudinary automatically.

## PDF Generation
- PDFs are generated with `xhtml2pdf` from HTML templates:
  - Appointment slip: `core/templates/core/appointment_pdf.html`
  - Prescription: `core/templates/core/prescription_pdf.html`
  - Invoice: `core/templates/core/invoice_pdf.html`

## Project Structure
- `hospitalms/` Django settings
- `core/` main application (models, views, templates)
- `docs/` database schema reference
- `render.yaml` Render blueprint
- `DEPLOY_RENDER.md` detailed Render deployment guide
