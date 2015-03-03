#encoding:UTF-8
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^sdstore/', include('sd_store.urls')),
    (r'^accounts/', include('basic_registration.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^', include('frontend.urls')),
)
