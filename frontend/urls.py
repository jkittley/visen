#encoding:UTF-8

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('frontend.views',
    url(r'^$', 'index', name='index'),
    url(r'raw/', 'raw', name='raw'),
    url(r'edit/([a-zA-Z0-9]+)/', 'edit', name='edit'),
    url(r'edit_input/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/', 'edit_input', name='edit_input'),
    url(r'delete_input/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/', 'delete_input', name='delete_input'),
    url(r'get_channels/([0-9]+)/', 'get_channels', name='get_channels'),
    url(r'view/([0-9]+)/', 'view', name='view'),
    url(r'ajax/([0-9]+)/', 'ajax', name='ajax'),
    url(r'clear_cache/([0-9]+)/', 'clear_cache', name='clear_cache'),
    url(r'init/', 'init', name='init'),
    url(r'sensor_info/', 'sensor_info', name='sensor_info'),
    url(r'addgeodata/', 'addgeodata', name='addgeodata'),
    url(r'help/', 'help', name='help'),
    
)   
