from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/home/live/', views.home_live_api, name='home_live_api'),
    path('api/home/doctors/', views.doctor_directory_api, name='doctor_directory_api'),
    path('api/home/callback/', views.callback_request_api, name='callback_request_api'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/staff/', views.manage_staff, name='manage_staff'),
    path('admin/doctors/', views.manage_doctors, name='manage_doctors'),
    path('admin/payments/', views.manage_payments, name='manage_payments'),
    path('admin/payments/<int:payment_id>/verify/', views.verify_payment, name='verify_payment'),
    path('admin/payments/<int:payment_id>/reject/', views.reject_payment, name='reject_payment'),

    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/availability/', views.availability_list, name='availability_list'),
    path('doctor/availability/add/', views.availability_create, name='availability_create'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('appointment/<int:appointment_id>/status/<str:status>/', views.update_appointment_status, name='update_appointment_status'),
    path('doctor/records/add/<int:patient_id>/', views.add_medical_record, name='add_medical_record'),
    path('doctor/prescription/<int:appointment_id>/', views.add_prescription, name='add_prescription'),
    path('doctor/invoice/<int:appointment_id>/', views.create_invoice, name='create_invoice'),

    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/book/', views.book_appointment, name='book_appointment'),
    path('patient/appointments/', views.patient_appointments, name='patient_appointments'),
    path('patient/payments/<int:payment_id>/proof/', views.payment_proof_upload, name='payment_proof_upload'),
    path('patient/report/upload/', views.upload_report, name='upload_report'),

    path('notifications/', views.notifications_panel, name='notifications_panel'),
    path('profile/', views.profile_settings, name='profile_settings'),
    path('api/dashboard/stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/read-all/', views.notifications_mark_all_read_api, name='notifications_mark_all_read_api'),
    path('api/notifications/<int:notification_id>/read/', views.notification_read_api, name='notification_read_api'),
    path('api/doctors/<int:doctor_id>/slots/', views.available_slots_api, name='available_slots_api'),

    path('pdf/appointment/<int:appointment_id>/', views.download_appointment_slip, name='appointment_pdf'),
    path('pdf/prescription/<int:prescription_id>/', views.download_prescription, name='prescription_pdf'),
    path('pdf/invoice/<int:invoice_id>/', views.download_invoice, name='invoice_pdf'),
]
