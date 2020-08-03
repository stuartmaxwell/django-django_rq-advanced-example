# Advanced Django-RQ Example

This builds on the previous basic [Django-RQ example](https://github.com/stuartmaxwell/django-django_rq-example) by adding a long-running task that is able to report its progress. In order to accurately report progress, you need to know how many things you need to do, and how many things you have completed. For example, if processing a CSV file with 1000 rows then you'll know which row you're currently on as well as how many rows in total. With this information you can create a percentage which becomes the progress. In this example, I added a simple sleep counter to the contact_form so that the task takes at least 60 seconds.

- First we edit the `contact_form > tasks.py` file by adding the sleep function which reports `progress` to the RQ job by using the `meta` field:

```python
from django.core.mail import send_mail, BadHeaderError
from djangorq_project.settings import DEFAULT_FROM_EMAIL
from django_rq import job
from rq import get_current_job

import logging
from time import sleep

logger = logging.getLogger(__name__)


@job
def send_email_task(to, subject, message):
    logger.info(f"from={DEFAULT_FROM_EMAIL}, {to=}, {subject=}, {message=}")

    job = get_current_job()

    secs = 30
    for sec in range(secs):
        progress = int(sec / secs * 100)
        job.meta["progress"] = progress
        job.save_meta()
        logger.debug(f"{job.meta['progress']=}")
        sleep(1)

    try:
        logger.info("About to send_mail")
        send_mail(subject, message, DEFAULT_FROM_EMAIL, [DEFAULT_FROM_EMAIL])
        job.meta["progress"] = 100
        job.save_meta()
    except BadHeaderError:
        logger.info("BadHeaderError")
    except Exception as e:
        logger.error(e)
```

- To enable the logging, we need to add a basic logging configuration in the project `settings.py` file:

```python
...
# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler",},},
    "root": {"handlers": ["console"], "level": "DEBUG",},
}
```

- Then we create a new view in `contact_form > views.py` that can be called to return the status and progress of a job as a JSON response. We also add in some logging so we can see what's happening in the console. The `ContactFormView` class gets some tweaks so that the `send_email` function returns the job object just created. This used to get the job ID which is passed to a new template that uses JavaScript to update the page based on the progress:

```python
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
```

- Create a new template to show the progress in `contact_form > templates > contact_form > progress.html`. The example below is a basic use of using vanilla JavaScript to retrieve the JSON response from the new view we have just created which is updated every second. You can extend this to show a pretty progress bar that changes its CSS width property with the progress reported.

```django
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Progress</title>
    </head>
    <body>
        <div id="app">
            <h2>Progress</h2>
            <div id="status"></div>
            <div id="progress"></div>
        </div>
        <script>
            var status_url = "{% url 'contact_form:job_status' job_id %}";
        </script>
        <script src="{% static 'js/progress.js' %}"></script>
    </body>
</html>
```

And here's the `progress.js` file using vanilla JS:

```javascript
// VanillaJS!!
function update_progress() {
  var status_div = document.querySelector("#status");
  var progress_div = document.querySelector("#progress");
  fetch(status_url)
    .then(function (response) {
      // The API call was successful!
      if (response.ok) {
        return response.json();
      }
      // There was an error
      return Promise.reject(response);
    })
    .then(function (data) {
      // This is the JSON from our response
      status = "Job status: " + data["status"];
      if (data["progress"] == null) {
        progress = "Progress: 0%";
      } else {
        progress = "Progress: " + data["progress"] + "%";
      }

      status_div.textContent = status;
      progress_div.textContent = progress;

      // Checks if the script is finished
      if (data["status"] == "finished") {
        status_div.textContent = status;
        progress_div.textContent = "Progress: 100%";
      } else if (data["status"] == "failed") {
        status_div.textContent = status;
        progress_div.textContent = "Progress: 100%";
      } else {
        setTimeout(function () {
          update_progress();
        }, 800);
      }
    })
    .catch(function (err) {
      // There was an error
      console.warn("Something went wrong.", err);
    });
}
update_progress();
```

- The last thing to do is to add a URL pattern in `contact_form > urls.py` for the new view we have created:

```python
from django.urls import path

from .views import ContactFormView, JobStatusView

app_name = "contact_form"
urlpatterns = [
    path("", ContactFormView.as_view(), name="contact_form"),
    path("taskstatus/<str:job_id>", JobStatusView.as_view(), name="job_status"),
]
```
