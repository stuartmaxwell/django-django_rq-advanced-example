from django.http import JsonResponse
from django.views import View
from django.views.generic import FormView
from django.shortcuts import render

import django_rq

import logging

from .forms import ContactFormModelForm
from .tasks import send_email_task

logger = logging.getLogger(__name__)


class ContactFormView(FormView):
    form_class = ContactFormModelForm
    template_name = "contact_form/contact_form.html"
    success_url = "/"

    def form_valid(self, form):
        form.save()
        job = self.send_email(form.cleaned_data)
        logger.debug(f"Job id: {job.id}")

        return render(self.request, "contact_form/progress.html", {"job_id": job.id},)

    def send_email(self, valid_data):
        email = valid_data["email"]
        subject = "Contact form sent from website"
        message = (
            f"You have received a contact form.\n"
            f"Email: {valid_data['email']}\n"
            f"Name: {valid_data['name']}\n"
            f"Subject: {valid_data['subject']}\n"
            f"{valid_data['message']}\n"
        )
        return send_email_task.delay(email, subject, message,)


class JobStatusView(View):
    def get(self, request, job_id):

        job = django_rq.get_queue().fetch_job(job_id)

        if job:
            response = {
                "status": job.get_status(),
                "progress": job.meta.get("progress", ""),
            }
            logger.debug(f"{job=}")
            logger.debug(f"{response=}")
        else:
            response = {"status": "invalid", "progress": ""}

        return JsonResponse(response)
