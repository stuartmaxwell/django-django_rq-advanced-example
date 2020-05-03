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
