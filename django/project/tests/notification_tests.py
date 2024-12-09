import copy
from unittest import mock
from unittest.mock import _CallList

from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from country.models import Donor, DonorCustomQuestion
from project.models import Project, Portfolio, ProjectPortfolioState, Stage
from project.tasks import project_still_in_draft_notification, published_projects_updated_long_ago, \
    project_review_requested_monthly_notification, project_review_requested_on_create_notification
from project.tests.setup import SetupTests
from user.models import UserProfile


class ProjectNotificationTests(SetupTests):

    def setUp(self):
        super(ProjectNotificationTests, self).setUp()

        self.user_1 = User.objects.create(username='bh_1', email='bh+1@pulilab.com')
        self.profile_1 = UserProfile.objects.create(user=self.user_1)
        self.user_2 = User.objects.create(username='bh_2', email='bh+2@pulilab.com')
        self.profile_2 = UserProfile.objects.create(user=self.user_2)
        self.user_3 = User.objects.create(username='bh_3', email='bh+3@pulilab.com')
        self.profile_3 = UserProfile.objects.create(user=self.user_3)
        self.user_4 = User.objects.create(username='bh_4', email='bh+4@pulilab.com')
        self.profile_4 = UserProfile.objects.create(user=self.user_4)
        self.user_5 = User.objects.create(username='bh_5', email='bh+5@pulilab.com')
        self.profile_5 = UserProfile.objects.create(user=self.user_5)

        self.published_project_data = dict(
            country=self.country.id, country_office=self.country_office.id,
            organisation=self.org.id, hsc_challenges=[1, 2], platforms=[1, 2],
            capability_categories=[], capability_levels=[], capability_subcategories=[])

        self.unicef, _ = Donor.objects.get_or_create(name='UNICEF')
        self.custom_question = DonorCustomQuestion.objects.create(
            question="Stage",
            donor_id=self.unicef.id,
            options=[
                "Opportunity and Ideation", "Preparation", "Analysis and Design", "Implementation Planning",
                "Developing or Adapting Solution", "Piloting and Evidence Generation", "Package and Champion",
                "Deploying", "Scaling up", "Scale and Handover", "Under Review", "Discontinued"
            ]
        )

    @mock.patch('project.tasks.send_mail_wrapper', return_value=None)
    def test_project_still_in_draft_notification(self, send_mail_wrapper):
        now = timezone.now()
        number_of_stages = Stage.objects.count()
        stale_draft_projects = []

        # Create draft and published projects over 30 days ago. The draft ones should trigger reminders, regardless of stage completion
        with freeze_time(now - timezone.timedelta(days=40)):
            print(Stage.objects.all())
            for stage in Stage.objects.all():
                data = copy.deepcopy(self.published_project_data)
                data['stages'] = [{'id': stage.id, 'date': '2022-01-01', 'note': 'Completion note'}]

                draft_project = Project.objects.create(name=f'Stale draft project that has completed {stage.name} stage',
                                                       data=data,
                                                       public_id='')
                draft_project.team.add(self.profile_1)
                # The task should pick draft_project  up
                stale_draft_projects.append(draft_project)

                published_project = Project.objects.create(name=f'Stale published project that has completed {stage.name} stage',
                                                           data=data,
                                                           public_id=f'Published {stage.id}')
                published_project.team.add(self.profile_1)
                # The task should not pick published_project up because it's published

        # Create draft and published projects under 30 days ago. This test ensures that none of these recently updated
        # projects will trigger a reminder, regardless of publication status or completed stages.
        with freeze_time(now - timezone.timedelta(days=20)):
            for stage in Stage.objects.all():
                data = copy.deepcopy(self.published_project_data)
                data['stages'] = [{'id': stage.id, 'date': '2022-01-01', 'note': 'Completion note'}]

                draft_project = Project.objects.create(name=f'Recently updated d draft project that has completed {stage.name} stage',
                                                       data=data,
                                                       public_id='')
                draft_project.team.add(self.profile_1)

                published_project = Project.objects.create(name=f'Recently updated d published project that has completed {stage.name} stage',
                                                           data=data,
                                                           public_id=f'Published {stage.id}')
                published_project.team.add(self.profile_1)

       # profile_1 is now a team member of (4 x number_of_stages) projects.
       # This means one email should be sent to profile_1
       # 1 x number_of_stages projects are over 30 days old and draft, so should trigger a notification
       # 1 x number_of_stages projects are over 30 days old and published, so should NOT trigger a notification
       # 1 x number_of_stages projects are under 30 days old and draft, so should NOT trigger a notification
       # 1 x number_of_stages projects are under 30 days old and published, so should NOT trigger a notification

       # All stale_draft_projects should be included the list of projects to render in the email
        with override_settings(EMAIL_SENDING_PRODUCTION=True):
            project_still_in_draft_notification.apply()

            self.assertEqual(len(send_mail_wrapper.call_args_list), 1)

            for call in send_mail_wrapper.call_args_list:
                call_args = call[1]
                self.assertEqual(call_args['email_type'], 'reminder_common_template')
                self.assertEqual(call_args['language'], 'en')
                self.assertEqual(call_args['to'], self.user_1.email)
                self.assertEqual(call_args['context']['name'], self.profile_1.name)
                self.assertEqual(len(call_args['context']['projects']), len(stale_draft_projects))
                self.assertTrue(
                    all(project in call_args['context']['projects'] for project in stale_draft_projects),
                    "Missing project in reminder-to-publish-drafts notification"
                )

    @mock.patch('project.tasks.send_mail_wrapper', return_value=None)
    def test_published_projects_updated_long_ago(self, send_mail_wrapper):
        now = timezone.now()

        # Ensure the last two stages are final stages
        last_two_stages = list(Stage.objects.all().order_by('-order')[:2])[::-1]
        for stage in last_two_stages:
            stage.completion_marks_an_initiative_as_inactive = True
            stage.save()

        non_final_stage_ids = Stage.objects.filter(completion_marks_an_initiative_as_inactive=False).values_list('id', flat=True)
        final_stage_ids = Stage.objects.filter(completion_marks_an_initiative_as_inactive=True).values_list('id', flat=True)

        # Create a  published project that is old enough to trigger a reminder and is current (i.e. has not completed a final stage)
        # This should trigger a notification
        with freeze_time(now - timezone.timedelta(days=200)): # old enough to trigger a reminder
            published_current_project_data = copy.deepcopy(self.published_project_data)
            published_current_project_data['stages'] = [{'id': non_final_stage_ids[0],
                                                         'date': '2022-01-01',
                                                         'note': 'Completion note'}]
            published_current_project = Project.objects.create(
                name='Published current project',
                data=published_current_project_data,
                public_id='1234')
            published_current_project.team.add(self.profile_1)

        # This project was modified recently so should not trigger a notification
        with freeze_time(now - timezone.timedelta(days=5)):
            published_current_recently_modified_project_data = copy.deepcopy(self.published_project_data)
            published_current_recently_modified_project_data['stages'] = [{'id': non_final_stage_ids[0],
                                                                           'date': '2022-01-01',
                                                                           'note': 'Completion note'}]
            published_recently_modified_current_project = Project.objects.create(
                name='Published current recently modified project',
                data=published_current_recently_modified_project_data,
                public_id='4321')
            published_recently_modified_current_project.team.add(self.profile_1)

        # This project is soft deleted so should not trigger a notification
        with freeze_time(now - timezone.timedelta(days=200)): # old enough to trigger a reminder
            published_current_project_data = copy.deepcopy(self.published_project_data)
            published_current_project_data['stages'] = [{'id': non_final_stage_ids[0],
                                                         'date': '2022-01-01',
                                                         'note': 'Completion note'}]
            deleted_published_current_project = Project.objects.create(
                name='Deleted published current project',
                data=published_current_project_data,
                public_id='1111')
            deleted_published_current_project.team.add(self.profile_1)
            deleted_published_current_project.delete()

        # This project has completed a final stage so should not trigger a notification
        with freeze_time(now - timezone.timedelta(days=200)): # old enough to trigger a reminder
            published_finished_project_data = copy.deepcopy(self.published_project_data)
            published_finished_project_data['stages'] = [{'id': final_stage_ids[0],
                                                          'date': '2022-02-02', 'note':
                                                          'Completion note for final stage'}]
            published_finished_project = Project.objects.create(
                name='Published finished project',
                data=published_finished_project_data,
                public_id='5678')
            published_finished_project.team.add(self.profile_2)

        # This should not trigger a notification because it is a draft project
        with freeze_time(now - timezone.timedelta(days=200)): # old enough to trigger a reminder
            draft_current_project_data = copy.deepcopy(self.published_project_data)
            draft_current_project_data['stages'] = [{'id': non_final_stage_ids[0],
                                                     'date': '2022-01-01',
                                                     'note': 'Completion note'}]
            draft_current_project = Project.objects.create(
                name='Draft current project',
                data=draft_current_project_data,
                public_id='')
            draft_current_project.team.add(self.profile_1)

        # This project has completed a final stage so should not trigger a notification
        with freeze_time(now - timezone.timedelta(days=200)): # old enough to trigger a reminder
            draft_finished_project_data = copy.deepcopy(self.published_project_data)
            draft_finished_project_data['stages'] = [{'id': final_stage_ids[0],
                                                      'date': '2022-02-02', 'note':
                                                      'Completion note for final stage'}]
            draft_finished_project = Project.objects.create(
                name='Draft final project',
                data=draft_finished_project_data,
                public_id='')
            draft_finished_project.team.add(self.profile_2)

        with override_settings(EMAIL_SENDING_PRODUCTION=True):
            published_projects_updated_long_ago.apply()

            # task should send one email: to the single team member of published_current_project
            self.assertEqual(len(send_mail_wrapper.call_args_list), 1)

            for call in send_mail_wrapper.call_args_list:
                call_args = call[1]
                self.assertEqual(call_args['email_type'], 'reminder_common_template')
                self.assertEqual(call_args['language'], 'en')
                # if call_args['to'] == self.user_1.email:
                    # user_1 should receive notifications about published project 1
                self.assertEqual(call_args['context']['name'], self.profile_1.name)
                self.assertEqual(len(call_args['context']['projects']), 1)
                self.assertIn(published_current_project, call_args['context']['projects'])

    @mock.patch('project.tasks.send_mail_wrapper', return_value=None)
    def test_project_review_monthly_reminder(self, send_mail_wrapper):
        now = timezone.now()

        with freeze_time(now - timezone.timedelta(days=45)):
            # create project
            published_project_1 = Project.objects.create(
                name='Published project 1', data=self.published_project_data, public_id='1111')
            published_project_1.team.add(self.profile_1)
            published_project_2 = Project.objects.create(
                name='Published project 2', data=self.published_project_data, public_id='1112')
            published_project_2.team.add(self.profile_1)
            published_project_3 = Project.objects.create(
                name='Published project 3', data=self.published_project_data, public_id='1113')
            published_project_3.team.add(self.profile_1)
            # create portfolio
            portfolio_1 = Portfolio.objects.create(name="Notification test portfolio")
            # create reviews
            pps_1 = ProjectPortfolioState.objects.create(project=published_project_1, portfolio=portfolio_1)
            pps_2 = ProjectPortfolioState.objects.create(project=published_project_2, portfolio=portfolio_1)
            pps_3 = ProjectPortfolioState.objects.create(project=published_project_3, portfolio=portfolio_1)
            reviewscore_1, _ = pps_1.assign_questionnaire(self.profile_1)
            reviewscore_2, _ = pps_2.assign_questionnaire(self.profile_2)
            reviewscore_3, _ = pps_3.assign_questionnaire(self.profile_2)
        with freeze_time(now - timezone.timedelta(days=10)):
            # task shouldn't pick this up
            reviewscore_4, _ = pps_2.assign_questionnaire(self.profile_1)

        with override_settings(EMAIL_SENDING_PRODUCTION=True):
            project_review_requested_monthly_notification.apply()

            # task should send emails about Published project 1 and 2-3
            self.assertEqual(len(send_mail_wrapper.call_args_list), 2)

            for call in send_mail_wrapper.call_args_list:
                call_args = call[1]
                self.assertEqual(call_args['email_type'], 'reminder_project_review_template')
                self.assertEqual(call_args['language'], 'en')

                if call_args['to'] == self.user_1.email:
                    # user_1 should receive notifications about published project 1
                    self.assertEqual(call_args['context']['name'], self.profile_1.name)
                    self.assertEqual([reviewscore_1], call_args['context']['reviewscores'])
                else:
                    # user_2 should receive notifications about published project 2
                    self.assertEqual(call_args['context']['name'], self.profile_2.name)
                    self.assertEqual({reviewscore_2, reviewscore_3}, set(call_args['context']['reviewscores']))
        # init
        send_mail_wrapper.call_args_list = _CallList()

        with override_settings(EMAIL_SENDING_PRODUCTION=False):
            project_review_requested_monthly_notification.apply()

            # task should send email about Published project 1
            self.assertEqual(len(send_mail_wrapper.call_args_list), 1)
            call_args_list = send_mail_wrapper.call_args_list[0][1]
            self.assertEqual(call_args_list['email_type'], 'reminder_project_review_template')
            self.assertEqual(call_args_list['to'], self.user_1.email)
            self.assertEqual([reviewscore_1], call_args_list['context']['reviewscores'])

    @mock.patch('project.tasks.send_mail_wrapper', return_value=None)
    def test_project_review_on_create_reminder(self, send_mail_wrapper):
        # create project
        published_project_1 = Project.objects.create(
            name='Published project 1', data=self.published_project_data, public_id='1111')
        published_project_1.team.add(self.profile_1)
        # create portfolio
        portfolio_1 = Portfolio.objects.create(name="Notification test portfolio")
        # create review
        pps_1 = ProjectPortfolioState.objects.create(project=published_project_1, portfolio=portfolio_1)
        reviewscore_1, _ = pps_1.assign_questionnaire(self.profile_1)

        project_review_requested_on_create_notification(reviewscore_1.id, "Testing!")

        # task should send email about Published project 1
        self.assertEqual(len(send_mail_wrapper.call_args_list), 1)
        call_args = send_mail_wrapper.call_args_list[0][1]
        self.assertEqual(call_args['email_type'], 'reminder_project_review_template')
        self.assertEqual(call_args['context']['name'], self.profile_1.name)
        self.assertEqual(call_args['language'], 'en')
        self.assertEqual([reviewscore_1], call_args['context']['reviewscores'])
