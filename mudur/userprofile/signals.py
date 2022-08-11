import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import signals
from mudur.adaptor import define_crontab, deleteoldjobs
from mudur.backend import create_verification_link, send_email_by_operation_name
from mudur.helpers import disable_for_loaddata
from mudur.models import ApprovalDate, Site
from mudur.settings import DJANGO_ROOT, VIRTUAL_ENV_PATH
from training.tutils import daterange

from userprofile.models import UserFeedback, UserVerification

log = logging.getLogger(__name__)


@disable_for_loaddata
def send_confirm_link(instance, created, **kwargs):
    if not instance.is_staff:
        if created:
            instance.is_active = False
            user_verification, created = UserVerification.objects.get_or_create(user=instance)
            user_verification.activation_key = create_verification_link(instance)
            user_verification.save()
            context = {
                "user": instance,
                "activation_key": user_verification.activation_key,
                "site": Site.objects.get(is_active=True),
                "recipientlist": [instance.username],
            }
            context["domain"] = context["site"].home_url.rstrip("/")
            send_email_by_operation_name(context, "send_activation_key")


@disable_for_loaddata
def defineconsentmailcronjob_signal(instance, created, **kwargs):
    """
    Site modelinde her save işlemi sonrasında "kabul e-postalarının onaylama tarihi bitiminde  e-postası
    gönderilmemis kullanicilara e-posta gonderilebilmesi icin" cronjob tanimlaması yapılıyor.
    """
    if instance.is_active:
        allapprovedates = ApprovalDate.objects.filter(site=instance, for_instructor=True).order_by("-end_date")
        if allapprovedates:
            eventstartdate = instance.event_start_date
            date_list = daterange(datetime.date(allapprovedates[0].end_date), eventstartdate)
            consentmailcommand = "cd %s && bash_scripts/abkayit_cronjob.sh -w %s -pv %s -f send_all_consent_email" % (
                DJANGO_ROOT,
                DJANGO_ROOT,
                VIRTUAL_ENV_PATH,
            )
            deleteoldjobs(consentmailcommand)
            for d in date_list:
                define_crontab(consentmailcommand, d)
                log.info(
                    "consentmailtotrainess_cronjob defined for date %s" % d.strftime("%Y-%m-%d %H:%M:%S"),
                    extra={"clientip": "", "user": ""},
                )


@disable_for_loaddata
def definenotapprovedtrainesscronjob_signal(instance, created, **kwargs):
    """
    Site modelinde her save işlemi sonrasında "kabul e-postalarının onaylama tarihi bitiminde  e-postası
    gönderilmemis kullanicilara e-posta gonderilebilmesi icin" cronjob tanimlaması yapılıyor.
    """
    if instance.is_active:
        beforeeventstartdate = instance.event_start_date - timedelta(days=0, hours=12)
        notapprovedcommand1 = (
            "cd %s && bash_scripts/abkayit_cronjob.sh -w %s -pv %s -f not_approved_trainess_eventstardate"
            % (DJANGO_ROOT, DJANGO_ROOT, VIRTUAL_ENV_PATH)
        )
        deleteoldjobs(notapprovedcommand1)
        define_crontab(notapprovedcommand1, beforeeventstartdate)
        log.info(
            "not_approved_trainess_eventstardate defined for date %s" % beforeeventstartdate,
            extra={"clientip": "", "user": ""},
        )
        allapprovedates = ApprovalDate.objects.filter(site=instance, for_instructor=True).order_by("-end_date")
        if allapprovedates:
            notapprovedcommand2 = (
                "cd %s && bash_scripts/abkayit_cronjob.sh -w %s -pv %s -f not_approved_trainess_after_approval_period_ends"
                % (DJANGO_ROOT, DJANGO_ROOT, VIRTUAL_ENV_PATH)
            )
            deleteoldjobs(notapprovedcommand2)
            define_crontab(notapprovedcommand2, allapprovedates[0].end_date + timedelta(days=1))
            log.info(
                "not_approved_trainess_after_approval_period_ends defined "
                "for date %s" % (allapprovedates[0].end_date + timedelta(days=1)),
                extra={"clientip": "", "user": ""},
            )


@disable_for_loaddata
def send_notice_for_user_feedback(instance, created, **kwargs):
    if created:
        context = {
            "user": instance.user,
            "title": instance.title,
            "body": instance.body,
            "site": Site.objects.get(is_active=True),
            "recipientlist": [settings.REPORT_RECIPIENT_LIST],
        }
        send_email_by_operation_name(context, "notice_for_user_feedback")


@disable_for_loaddata
def send_answer_for_user_feedback(instance, created, **kwargs):
    if instance.status == UserFeedback.STATUS_CLOSED:
        context = {
            "user": instance.user,
            "title": instance.title,
            "body": instance.body,
            "answer": instance.answer,
            "site": Site.objects.get(is_active=True),
            "recipientlist": [instance.user.user.username],
        }
        send_email_by_operation_name(context, "answer_for_user_feedback")


signals.post_save.connect(send_confirm_link, sender=User)
signals.post_save.connect(defineconsentmailcronjob_signal, sender=Site)
signals.post_save.connect(definenotapprovedtrainesscronjob_signal, sender=Site)
signals.post_save.connect(send_notice_for_user_feedback, sender=UserFeedback)
signals.post_save.connect(send_answer_for_user_feedback, sender=UserFeedback)
