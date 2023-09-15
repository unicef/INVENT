from __future__ import unicode_literals

import requests

from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.views import TokenAuthMixin
from .provider import AzureProvider
from .tasks import fetch_users_from_aad_and_update_db


LOGIN_URL = f'https://login.microsoftonline.com/{getattr(settings, "SOCIALACCOUNT_AZURE_TENANT", "common")}/oauth2/v2.0'
GRAPH_URL = "https://graph.microsoft.com/v1.0"


class AzureOAuth2Adapter(OAuth2Adapter):
    """
    Docs available at:
    https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-v2-protocols
    """
    print('inside AzureOAuth2Adapter')
    provider_id = AzureProvider.id
    access_token_url = LOGIN_URL + "/token"
    authorize_url = LOGIN_URL + "/authorize"
    profile_url = "https://graph.microsoft.com/v1.0/me"
    # Can be used later to obtain group data. Needs 'Group.Read.All' or
    # similar.
    #
    # See https://developer.microsoft.com/en-us/graph/docs/api-reference/beta/api/user_list_memberof  # noqa
    groups_url = GRAPH_URL + "/me/memberOf?$select=displayName"

    def complete_login(self, request, app, token, **kwargs):
        print('inside AzureOAuth2Adapter.complete_login')
        headers = {"Authorization": "Bearer {0}".format(token.token)}
        extra_data = {}
        print(f'headers inside AzureOAuth2Adapter.complete_login: {headers}')
        resp = requests.get(self.profile_url, headers=headers)

        # See:
        #
        # https://developer.microsoft.com/en-us/graph/docs/api-reference/v1.0/api/user_get  # noqa
        #
        # example of what's returned (in python format)
        #
        # {u'displayName': u'John Smith', u'mobilePhone': None,
        #  u'preferredLanguage': u'en-US', u'jobTitle': u'Director',
        #  u'userPrincipalName': u'john@smith.com',
        #  u'@odata.context':
        #  u'https://graph.microsoft.com/v1.0/$metadata#users/$entity',
        #  u'officeLocation': u'Paris', u'businessPhones': [],
        #  u'mail': u'john@smith.com', u'surname': u'Smith',
        #  u'givenName': u'John', u'id': u'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'}

        profile_data = resp.json()
        print(f'profile_data inside AzureOAuth2Adapter.complete_login: {profile_data}')
        extra_data.update(profile_data)
        print(f'extra_data inside AzureOAuth2Adapter.complete_login: {extra_data}')
        return self.get_provider().sociallogin_from_response(request, extra_data)


class UpdateAADUsersView(TokenAuthMixin, APIView):
    """
    API View to update and save Azure Active Directory (AAD) users in the local database.
    It fetches the AAD users, saves them, and returns the updated users' profiles.
    Requires token authentication.
    """

    def put(self, request, format=None):
        # Default to 100 if not provided
        max_users = request.data.get("max_users", None)
        # Call the Celery task and pass max_users as a parameter
        fetch_users_from_aad_and_update_db.delay(max_users)

        return Response(
            {"message": "Initiated celery task fetch_users_from_aad_and_update_db."},
            status=status.HTTP_202_ACCEPTED,
        )


oauth2_login = OAuth2LoginView.adapter_view(AzureOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(AzureOAuth2Adapter)
