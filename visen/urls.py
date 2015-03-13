#encoding:UTF-8
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^sdstore/', include('sd_store.urls')),
    (r'^accounts/', include('basic_registration.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^', include('frontend.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

