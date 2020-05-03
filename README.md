# Basic Django-RQ Example

You could git clone this repository to get it working but I recommend following these manual steps so you understand what's required to get a basic Django-RQ example up and running.

- Before you start, you'll need a Redis server. If you don't have one the easiest way is through Docker with the following command:

```bash
docker run --name my-redis-server -d -p 127.0.0.1:6379:6379 redis
```

- Create a virtual environment using the method of your choice, I like to use the following command:

```bash
python3.8 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip wheel setuptools > /dev/null
```

- Create the requirements.txt file to install the packages required:

```
django
redis
django-rq
```

- Activate your virtual environment and install the requirements in the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

- Create your Django project:

```bash
django-admin startproject djangorq_project .
```

- Open the `settings.py` file and add Django Q to the list of installed apps to complete installation.

```python
INSTALLED_APPS = [
    ...
    "django_rq",
]
```

- Open the project `urls.py` file and add the Django-RQ URLs to complete installation.

```python
urlpatterns = [
    ...
    path("django-rq/", include("django_rq.urls")),
]
```

- Add the Django-RQ configuration in the `settings.py` file:

```python
# Django-RQ Configuration
RQ_QUEUES = {
    "default": {"HOST": "localhost", "PORT": 6379, "DB": 0, "DEFAULT_TIMEOUT": 360,},
}
```

- That's the base project configuration complete, run the database migrations and create a superuser:

```bash
python manage.py migrate
python manage.py createsuperuser
```

- Add a new app, we'll make a basic contact form app that stores messages in our database and sends an email to the site owner:

```bash
django-admin startapp contact_form
```

- Add some email configuration to the `settings.py` file. I use Amazon SES but substitute with our own SMTP settings.

```python
# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = ""  # add your own settings here
EMAIL_PORT = ""  # add your own settings here
EMAIL_HOST_USER = ""  # add your own settings here
EMAIL_HOST_PASSWORD = ""  # add your own settings here
EMAIL_USE_TLS = True  # add your own settings here
DEFAULT_FROM_EMAIL = "you@example.com"  # your email address
```

- While you're in the settings, add your new app to the `INSTALLED_APPS` section:

```python
INSTALLED_APPS = [
    ...
    "contact_form.apps.ContactFormConfig",
]
```

- Create a model to store the messages sent from the website in `contact_form > models.py`

```python
from django.db import models


class ContactForm(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=64)
    subject = models.CharField(max_length=64)
    message = models.TextField()
    created_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contactform"
        verbose_name = "contact form message"
        verbose_name_plural = "contact form messages"

    def __str__(self):
        return self.email
```

- Expose the model in the Admin site with `contact_form > admin.py`

```python
from django.contrib import admin

from .models import ContactForm


class ContactFormAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "subject", "created_on")


admin.site.register(ContactForm, ContactFormAdmin)
```

- Create a contact form in `contact_form > forms.py` (you'll need to create this file):

```python
from django.forms import ModelForm

from .models import ContactForm


class ContactFormModelForm(ModelForm):
    class Meta:
        model = ContactForm
        fields = ["name", "email", "subject", "message"]
```

- Create the Django-RQ task to send an email in `contact_form > tasks.py` (you'll need to create this file):

```python
from django.core.mail import send_mail, BadHeaderError
from djangoq_project.settings import DEFAULT_FROM_EMAIL
import logging

logger = logging.getLogger(__name__)


def send_email_task(self, to, subject, message):
    logger.info(f"from={DEFAULT_FROM_EMAIL}, {to=}, {subject=}, {message=}")
    try:
        logger.info("About to send_mail")
        send_mail(subject, message, DEFAULT_FROM_EMAIL, [DEFAULT_FROM_EMAIL])
    except BadHeaderError:
        logger.info("BadHeaderError")
    except Exception as e:
        logger.error(e)
```

- Create a basic template to use: `contact_form > templates > contact_form > contact_form.html` (you'll need to create these folders and file):

```django
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Contact Form</title>
    </head>
    <body>
        <h2>Contact Form</h2>
        <form method="post" action="">
            {% csrf_token %}
            {{ form.as_p }}
            <input type="submit" value="Send Message">
        </form>
    </body>
</html>
```

- Create a view in `contact_form > views.py`

```python
from django.views.generic import FormView

from .forms import ContactFormModelForm
from .tasks import send_email_task


class ContactFormView(FormView):
    form_class = ContactFormModelForm
    template_name = "contact_form/contact_form.html"
    success_url = "/"

    def form_valid(self, form):
        form.save()
        self.send_email(form.cleaned_data)

        return super().form_valid(form)

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
        send_email_task.delay(email, subject, message,)
```

- Create a URLs configuration in `contact_form > urls.py` (you'll need to create this file):

```python
from django.urls import path

from .views import ContactFormView

app_name = "contact_form"
urlpatterns = [
    path("", ContactFormView.as_view(), name="contact_form"),
]
```

- Update the project URLs to reference these new URLs in `djangorq_project > urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("contact_form.urls")),
]
```

- Create and apply the database migrations for the new model

```bash
python manage.py makemigrations
python manage.py migrate
```

- Now you need to launch the Django test server:

```bash
python manage.py runserver
```

- Then in a second terminal window, navigate to your project directory, activate the virtual environment again, and then launch the Django-RQ rqworker process - it should print out some debug information and then a `Lisenting on default...` message to indicate it has connected to Redis successfully and is waiting for tasks:

```bash
python manage.py rqworker default
```

- Browse to http://127.0.0.1 and you should see a contact form. Try sending a message to see if it works.

- Switch back to your terminal windows with the Django-RQ process and you'll see some updates. It can take several seconds to send the email, but that was all done by the rqworker process and didn't affect the page loading time after submitting the form.

- After sending a message, log in to the admin site (http://127.0.0.1/admin) and take a look at the contact form model we created.

Hopefully that worked for you and gives you something to build upon.
