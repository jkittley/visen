# encoding: utf-8

from django.conf.urls.defaults import patterns, url, include
from views import profile_view
from django.contrib.auth.views import password_change, password_reset_confirm

urlpatterns = patterns('logserver.views',
    url(r'^profile/$', profile_view, name='profile_view'),
    url(r'^password/change/$', password_change, name='auth_password_change'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                           password_reset_confirm, name='auth_password_reset_confirm'),
    (r'^', include('registration.backends.default.urls')),
)
