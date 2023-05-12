import requests
from time import sleep

from allauth.account.utils import setup_user_email
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.account.adapter import DefaultAccountAdapter
from rest_auth.registration.views import SocialLoginView

from .models import UserProfile
from azure.views import AzureOAuth2Adapter
from country.models import Country
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from django.db import IntegrityError
from django.db.models import Q

# This has to stay here to use the proper celery instance with the djcelery_email package
import scheduler.celery  # noqa


class DefaultAccountAdapterCustom(DefaultAccountAdapter):
    def validate_unique_email(self, email):  # pragma: no cover
        return email


class AzureLogin(SocialLoginView):
    adapter_class = AzureOAuth2Adapter
    callback_url = settings.SOCIALACCOUNT_CALLBACK_URL
    client_class = OAuth2Client


class MyAzureAccountAdapter(DefaultSocialAccountAdapter):  # pragma: no cover
    def save_user(self, request, sociallogin, form=None):
        u = sociallogin.user
        u.set_unusable_password()
        DefaultAccountAdapterCustom().populate_username(request, u)
        assert not sociallogin.is_existing
        user = sociallogin.user
        name = sociallogin.account.extra_data.get('displayName')
        job_title = sociallogin.account.extra_data.get('jobTitle')
        department = sociallogin.account.extra_data.get('department')
        country = sociallogin.account.extra_data.get('country')

        user_model = get_user_model()
        try:
            old_user = user_model.objects.filter(email=user.email).get()
        except user_model.DoesNotExist:
            user.save()
            sociallogin.account.user = user
            sociallogin.account.save()
            UserProfile.objects.create(
                user=user,
                name=name,
                account_type=UserProfile.DONOR,
                job_title=job_title,
                department=department,
                country=country
            )
            setup_user_email(request, user, sociallogin.email_addresses)
        else:
            sociallogin.account.user = old_user
            sociallogin.account.save()
            sociallogin.user = old_user
            if not old_user.userprofile.name:
                old_user.userprofile.name = name
                old_user.userprofile.job_title = job_title
                old_user.userprofile.department = department
                old_user.userprofile.save()

        return user

    def save_aad_users(self, azure_users):
        """
        This method updates the application's user database with information fetched from Azure AD.
        It processes the users in batches to increase efficiency and reduce potential for errors or timeouts.

        It separates out new users and existing users to handle them differently, creating new user entries for new users 
        and updating existing entries for existing users. It uses Django's `bulk_create` and `bulk_update` methods 
        to perform these operations more efficiently.

        The whole process for each batch is wrapped in a database transaction to ensure data integrity. 
        If any part of the process fails, the transaction will be rolled back to the state it was in before the transaction started.

        Parameters:
            azure_users (list): A list of dictionaries where each dictionary represents a user fetched from Azure AD. 
            Each dictionary contains user attributes like email, name, job title, department, country, etc.

        Returns:
        list: A list of UserProfile objects that were updated or created in the process.
        """
        # Get the User model
        user_model = get_user_model()

        # Set the number of users to process in each batch
        batch_size = 1000

        # Initialize a list to hold the users that have been updated
        updated_users = []

        # Process the users in batches
        for i in range(0, len(azure_users), batch_size):
            # Create a batch of users to process
            batch = azure_users[i:i + batch_size]

            # Initialize lists to hold data for new and existing users
            new_users_data = []
            existing_users_data = []

            # Get a set of existing email addresses
            existing_emails = set(
                user_model.objects.values_list('email', flat=True))

            # Separate the users in the batch into new and existing users
            for azure_user in batch:
                # Create a dictionary to hold the user's data
                user_data = {
                    'email': azure_user['mail'],
                    'username': azure_user['mail'],
                    'name': azure_user['displayName'],
                    'job_title': azure_user['jobTitle'],
                    'department': azure_user['department'],
                    'country_name': azure_user['country'],
                    'social_account_uid': azure_user['id'],
                }
                # Check if the user's email is already in the database
                if user_data['email'] in existing_emails:
                    existing_users_data.append(user_data)
                else:
                    new_users_data.append(user_data)

            # Create new users and social accounts
            new_users = []
            user_profiles = []
            social_accounts = []

            # Create a new User, UserProfile, and SocialAccount for each new user
            for user_data in new_users_data:
                # Get or create the user's country
                country, _ = Country.objects.get_or_create(
                    name=user_data['country_name'])

                # Create a new User
                user = user_model(
                    email=user_data['email'], username=user_data['username'])
                user.set_unusable_password()

                # Create a new UserProfile
                user_profiles.append(UserProfile(
                    user=user,
                    name=user_data['name'],
                    job_title=user_data['job_title'],
                    department=user_data['department'],
                    country=country,
                    account_type=UserProfile.DONOR,
                    social_account_uid=user_data['social_account_uid']
                ))

                # Create a new SocialAccount
                social_accounts.append(SocialAccount(
                    user=user, provider='azure', uid=user_data['social_account_uid']))

                new_users.append(user)

            # Use a transaction to create the new users, user profiles, and social accounts
            try:
                with transaction.atomic():
                    user_model.objects.bulk_create(new_users)
                    UserProfile.objects.bulk_create(user_profiles)
                    SocialAccount.objects.bulk_create(social_accounts)
            except Exception as e:
                # Log any errors that occur during the creation process
                print(f'Error while creating users: {e}')

            # Initialize a list to hold the users that need to be updated
            to_be_updated = []
            for user_data in existing_users_data:
                user = user_model.objects.get(email=user_data['email'])
                country, _ = Country.objects.get_or_create(
                    name=user_data['country_name'])
                user_profile = UserProfile.objects.get(user=user)

                # Update the user's profile
                user_profile.name = user_data['name']
                user_profile.job_title = user_data['job_title']
                user_profile.department = user_data['department']
                user_profile.country = country
                user_profile.social_account_uid = user_data['social_account_uid']

                # Add the updated profile to the list of profiles to be updated
                to_be_updated.append(user_profile)

            # Use a transaction to update the user profiles
            try:
                with transaction.atomic():
                    # bulk_update is used to perform the updates in a single query for efficiency
                    UserProfile.objects.bulk_update(to_be_updated, [
                                                    'name', 'job_title', 'department', 'country', 'social_account_uid'])
                    # Add the updated profiles to the list of all updated users
                    updated_users.extend(to_be_updated)
            except Exception as e:
                # Log any errors that occur during the update process
                print(f'Error while updating users: {e}')

        # Return the list of updated users
        return updated_users

    def get_aad_users(self):
        """
        Retrieves Azure Active Directory (AAD) users using Microsoft's Graph API.

        This function sends GET requests to the Graph API endpoint for users, handling pagination 
        by following the '@odata.nextLink' URL included in the response until no such link is present.
        If the request fails, it retries up to 5 times with exponential backoff to handle temporary issues.

        The function requires an access token which is fetched using the `get_access_token` method. 
        The users are returned as a list of dictionaries in the format provided by the Graph API.

        Returns:
            list: A list of dictionaries where each dictionary represents an AAD user.

        Raises:
            requests.exceptions.RequestException: If a request to the Graph API fails.
        """
        # Define the endpoint URL.
        url = 'https://graph.microsoft.com/v1.0/users?$top=1000'

        # Get the access token.
        token = self.get_access_token()

        # Prepare the request headers.
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Initialize an empty list to hold the users.
        users = []

        # Initialize the retry count to 0.
        retry_count = 0

        # Keep sending requests as long as there's a next page URL and the retry limit hasn't been reached.
        while url and retry_count < 5:
            try:
                # Send the request.
                response = requests.get(url, headers=headers)

                # Raise an exception if the request was unsuccessful.
                response.raise_for_status()

                # Parse the response JSON.
                response_data = response.json()

                # Add the users from the current page to the list.
                users.extend(response_data.get('value', []))

                # Get the URL for the next page.
                url = response_data.get('@odata.nextLink', None)

                # Reset the retry count after a successful request.
                retry_count = 0

                # Wait for 10 seconds to avoid hitting the rate limit.
                sleep(10)
            except requests.exceptions.RequestException as e:
                # Log the error and increment the retry count.
                print(f"Error while making request to {url}: {e}")
                retry_count += 1

                # Use exponential backoff when retrying.
                sleep(10 * (2 ** retry_count))

        # Return the list of users.
        return users

    def is_auto_signup_allowed(self, request, sociallogin):
        return True

    def get_access_token(self):
        tenant_id = settings.SOCIALACCOUNT_AZURE_TENANT
        client_id = settings.SOCIALACCOUNT_PROVIDERS['azure']['APP']['client_id']
        client_secret = settings.SOCIALACCOUNT_PROVIDERS['azure']['APP']['secret']
        resource = 'https://graph.microsoft.com'
        url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/token'

        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'resource': resource
        }

        response = requests.post(url, data=payload)
        if response.status_code == 200:
            json_response = response.json()
            access_token = json_response['access_token']
            return access_token
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
