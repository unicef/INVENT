from collections import defaultdict

from celery.utils.log import get_task_logger
from core.utils import send_mail_wrapper
from country.models import Country, Donor, DonorCustomQuestion
from scheduler.celery import app
from user.models import UserProfile

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Project, ReviewScore

logger = get_task_logger(__name__)


def exclude_specific_project_stages(projects, filter_key_prefix="draft"):
    try:
        unicef = Donor.objects.get(name="UNICEF")
    except Donor.DoesNotExist:  # pragma: no cover
        pass
    else:
        try:
            question = DonorCustomQuestion.objects.get(donor=unicef, question="Stage")
        except DonorCustomQuestion.DoesNotExist:  # pragma: no cover
            pass
        else:
            stages_to_exclude = ["Discontinued", "Scale and Handover"]
            filtered_projects = Project.objects.none()
            key = (
                f"{filter_key_prefix}__donor_custom_answers__{unicef.id}__{question.id}"
            )
            for stage in stages_to_exclude:
                condition = {f"{key}__icontains": stage}
                filtered_projects = filtered_projects | projects.filter(**condition)

            if filtered_projects:
                projects = projects.exclude(id__in=filtered_projects)
    return projects


@app.task(name="project_review_requested_on_create_notification")
def project_review_requested_on_create_notification(review_id, custom_msg=None):
    """
    Sends notification if a project needs review by an user - on create task
    """
    try:
        review = ReviewScore.objects.get(id=review_id)
    except ReviewScore.DoesNotExist:  # pragma: no cover
        pass
    else:
        send_mail_wrapper(
            subject=_("You have a new project review request"),
            email_type="reminder_project_review_template",
            to=review.reviewer.user.email,
            language=review.reviewer.language or settings.LANGUAGE_CODE,
            context={
                "reviewscores": [review],
                "name": review.reviewer.name,
                "details": _("Please review this project: "),
                "custom_msg": custom_msg,
            },
        )


@app.task(name="project_still_in_draft_notification")
def project_still_in_draft_notification():
    """
    Sends notification if a project is in draft state for over a month.
    """
    from user.models import UserProfile

    projects = Project.objects.draft_only().filter(
        modified__lt=timezone.now() - timezone.timedelta(days=31)
    )

    projects = exclude_specific_project_stages(projects)

    if not projects:  # pragma: no cover
        return

    # limit emails
    if not settings.EMAIL_SENDING_PRODUCTION:
        projects = Project.objects.filter(id=projects.first().id)

    project_team_members = set(projects.values_list("team", flat=True))

    for member in project_team_members:
        try:
            profile = UserProfile.objects.get(id=member)
        except UserProfile.DoesNotExist:  # pragma: no cover
            pass
        else:
            member_projects = [project for project in projects.filter(team=member)]
            subject = _("One or more of your projects have not been published yet")
            details = _(
                "The following project(s) have been draft only for over a month, "
                "please consider publishing so they become visible in the search or on the map: "
            )
            send_mail_wrapper(
                subject=subject,
                email_type="reminder_common_template",
                to=profile.user.email,
                language=profile.language or settings.LANGUAGE_CODE,
                context={
                    "projects": member_projects,
                    "name": profile.name,
                    "details": details,
                },
            )


@app.task(name="published_projects_updated_long_ago")
def published_projects_updated_long_ago():
    """
    Sends notification if a project is published but not updated in the last 6 months
    """
    from user.models import UserProfile

    projects = Project.objects.published_only().filter(
        modified__lt=timezone.now() - timezone.timedelta(days=180)
    )

    projects = exclude_specific_project_stages(projects, filter_key_prefix="data")

    if not projects:  # pragma: no cover
        return

    # limit emails
    if not settings.EMAIL_SENDING_PRODUCTION:
        projects = Project.objects.filter(id=projects.first().id)

    project_team_members = set(projects.values_list("team", flat=True))

    for member in project_team_members:
        try:
            profile = UserProfile.objects.get(id=member)
        except UserProfile.DoesNotExist:  # pragma: no cover
            pass
        else:
            member_projects = [project for project in projects.filter(team=member)]
            subject = _(
                "One or more of your projects have not been updated for 6 months"
            )
            details = _(
                "Please check in to keep the project data current by verifying the following project(s):"
            )
            send_mail_wrapper(
                subject=subject,
                email_type="reminder_common_template",
                to=profile.user.email,
                language=profile.language or settings.LANGUAGE_CODE,
                context={
                    "projects": member_projects,
                    "name": profile.name,
                    "details": details,
                },
            )


@app.task(name="send_project_approval_digest")
def send_project_approval_digest():
    countries = Country.objects.exclude(users=None)
    for country in countries:
        if country.project_approval:
            projects = Project.objects.filter(
                data__country=country.id, approval__approved__isnull=True
            )

            if not projects:
                return

            email_mapping = defaultdict(list)
            for profile in country.users.all():
                email_mapping[profile.language].append(profile.user.email)

            for language, email_list in email_mapping.items():
                context = {"country_name": country.name, "projects": projects}

                send_mail_wrapper(
                    subject="Action required: New projects awaiting approval",
                    email_type="status_report",
                    to=email_list,
                    language=language,
                    context=context,
                )


@app.task(name="notify_superusers_about_new_pending_approval")
def notify_superusers_about_new_pending_approval(class_name, object_id):
    klass = apps.get_model("project", class_name)
    object = klass.objects.get(id=object_id)

    email_mapping = defaultdict(list)

    
    if settings.APPROVAL_REQUEST_SEND_TO:
        email_mapping[settings.LANGUAGE_CODE].append(settings.APPROVAL_REQUEST_SEND_TO)
    else:
        super_users = User.objects.filter(is_superuser=True)
        for user in super_users:
            try:
                email_mapping[user.userprofile.language].append(user.email)
            except ObjectDoesNotExist:
                email_mapping[settings.LANGUAGE_CODE].append(user.email)

    change_url = reverse(
        "admin:project_{}_change".format(object._meta.model_name), args=(object.id,)
    )
    
    for language, email_list in email_mapping.items():
        send_mail_wrapper(
            subject=_(f"New {object._meta.model_name} is pending for approval"),
            email_type="new_pending_approval",
            to=email_list,
            language=language,
            context={
                "object_name": object.name,
                "change_url": change_url,
                "added_by": object.added_by,
            },
        )


@app.task(name="notify_user_about_approval")
def notify_user_about_approval(action, class_name, object_id, field_name):
    klass = apps.get_model("project", class_name)
    object = klass.objects.get(id=object_id)
    if not object.added_by:
        return
    
    if object.project:
        initiative_name=object.project.name
        initiative_id=object.project.id
    else:
        initiative_name=None
        initiative_id=None


    if action == "approve":
        email_type = "object_approved"
    elif action == "decline":
        email_type = "object_declined"
    else:
        return


    send_mail_wrapper(subject=_(f"Request for {field_name} tag"),
                      email_type=email_type,
                      to=object.added_by.user.email,
                      language=object.added_by.language or settings.LANGUAGE_CODE,
                      context={'object_name': object.name, 
                               'field_name': field_name,
                               'comment': object.comment,
                               'full_name': object.added_by.name,
                               'initiative_name':initiative_name,
                               'initiative_id':initiative_id,
                               'language':object.added_by.language or settings.LANGUAGE_CODE,}
                               )
