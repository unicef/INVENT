from django.conf import settings
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from allauth.account.views import confirm_email
from rest_framework_simplejwt.views import TokenObtainPairView # refresh token functionality can be added with TokenRefreshView

from . import views as views
from .adapters import AzureLogin

router = DefaultRouter()
router.register(r'userprofiles', views.UserProfileViewSet)
router.register(r'userprofiles', views.UserProfileListViewSet)
router.register(r'organisations', views.OrganisationViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("", include("django.contrib.auth.urls")),
    path('rest-auth/azure/', AzureLogin.as_view(), name='az_login'),
    path('api-token-auth/', views.CustomTokenObtainPairView.as_view(), name='api_token_auth'),
    re_path(r"^email-confirmation/(?P<key>\w+)/$", confirm_email, name="account_confirm_email"),
]

if settings.ENABLE_API_REGISTRATION:
    urlpatterns += [
        path("all-auth/", include("allauth.urls")),
        path("dj-rest-auth/", include('dj_rest_auth.urls')),
        path("dj-rest-auth/registration/", include("dj_rest_auth.registration.urls")),
    ]
