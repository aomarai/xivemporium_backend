"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from mods.views import (
    ModListAPIView,
    ModDetailAPIView,
    ModSearchByCategoryAPIView,
    ModSearchByTagAPIView,
    ModSearchByTitleAPIView,
    ModSearchByUserAPIView,
    ModCreateAPIView,
    TagListAPIView,
    RaceListAPIView,
    GenderListAPIView,
    ModUpdateAPIView,
    ModDeleteAPIView,
    ModSearchByRaceAPIView,
    ModSearchByGenderAPIView,
    UserRegistrationAPIView,
    ModApprovalAPIView,
)

BASE_MODS_URL = "m"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(BASE_MODS_URL, ModListAPIView.as_view(), name="list"),
    path(f"{BASE_MODS_URL}/create/", ModCreateAPIView.as_view(), name="create"),
    path(f"{BASE_MODS_URL}/<uuid:uuid>/", ModDetailAPIView.as_view(), name="detail"),
    path(f"{BASE_MODS_URL}/<uuid:uuid>/update/", ModUpdateAPIView.as_view(), name="update"),
    path(f"{BASE_MODS_URL}/<uuid:uuid>/delete/", ModDeleteAPIView.as_view(), name="delete"),
    path(f"{BASE_MODS_URL}/<uuid:uuid>/approve/", ModApprovalAPIView.as_view(), name="approve"),
    path(
        f"{BASE_MODS_URL}/category/<int:category_id>/", ModSearchByCategoryAPIView.as_view(), name="search-by-category"
    ),
    path(f"{BASE_MODS_URL}/tag/", ModSearchByTagAPIView.as_view(), name="search-by-tag"),
    path(f"{BASE_MODS_URL}/category/", ModSearchByCategoryAPIView.as_view(), name="search-by-category"),
    path(f"{BASE_MODS_URL}/title/<str:title>/", ModSearchByTitleAPIView.as_view(), name="search-by-title"),
    path(f"{BASE_MODS_URL}/user/<int:user_id>/", ModSearchByUserAPIView.as_view(), name="search-by-user"),
    path(f"{BASE_MODS_URL}/race/", ModSearchByRaceAPIView.as_view(), name="search-by-race"),
    path(f"{BASE_MODS_URL}/gender", ModSearchByGenderAPIView.as_view(), name="search-by-gender"),
    path("tags/", TagListAPIView.as_view(), name="tag-list"),
    path("races/", RaceListAPIView.as_view(), name="race-list"),
    path("genders/", GenderListAPIView.as_view(), name="gender-list"),
    path("register/", UserRegistrationAPIView.as_view(), name="register"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
