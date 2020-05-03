from django.core.mail import send_mail, BadHeaderError
from djangorq_project.settings import DEFAULT_FROM_EMAIL
from django_rq import job

import logging

logger = logging.getLogger(__name__)


@job
def send_email_task(to, subject, message):
    logger.info(f"from={DEFAULT_FROM_EMAIL}, {to=}, {subject=}, {message=}")
    try:
        logger.info("About to send_mail")
        send_mail(subject, message, DEFAULT_FROM_EMAIL, [DEFAULT_FROM_EMAIL])
    except BadHeaderError:
        logger.info("BadHeaderError")
    except Exception as e:
        logger.error(e)
