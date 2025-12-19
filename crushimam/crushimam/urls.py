"""
URL configuration for crushimam project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from . import views
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('confessions.urls')),
    path('privacy-policy/', views.privacy_and_policy, name='privacy_and_policy'),
]

if settings.DEBUG:
    # During development serve static files directly from STATICFILES_DIRS
    # (the project `static/` folder) rather than STATIC_ROOT which is
    # normally populated by `collectstatic` for production.
    static_root = None
    try:
        static_root = settings.STATICFILES_DIRS[0]
    except Exception:
        static_root = settings.STATIC_ROOT

    urlpatterns += static(settings.STATIC_URL, document_root=static_root)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)