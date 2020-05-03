from django.urls import path

from .views import ContactFormView, JobStatusView

app_name = "contact_form"
urlpatterns = [
    path("", ContactFormView.as_view(), name="contact_form"),
    path("taskstatus/<str:job_id>", JobStatusView.as_view(), name="job_status"),
]
