# -*- coding: UTF-8 -*-
from django.conf.urls.defaults import patterns

urlpatterns = patterns('sd_store.views.general',
    
    (r'^login','login_view'),
    (r'^logout','logout_view'),
    
    (r'^users/$','user_view'),
    #(r'^user/(?P<user_id>[-\w]+)/$','user_view'),
    
    (r'^sensors/$','sensor_view'),
    (r'^sensor/(?P<sensor_id>[-\w]+)/$','sensor_view'),
    (r'^sensor/(?P<sensor_id>[-\w]+)/(?P<channel_name>[-\w]+)/$','channel_view'),
    (r'^sensor/(?P<sensor_id>[-\w]+)/(?P<channel_name>[-\w]+)/data/$','data_view'),
    (r'^sensor/(?P<sensor_id>[-\w]+)/(?P<channel_name>[-\w]+)/last-reading/$','last_reading_view'),

    (r'^rawinput/sensor/(?P<sensor_mac>[-\w]+)/(?P<channel_name>[-\w]+)/data/','raw_data_view'),
    
    (r'^meters','meter_view'),
    (r'^meter/(?P<meter_id>[-\w]+)/$','meter_view'),
    
    (r'^meteringPoints','metering_point_view'),
    (r'^meteringPoint/(?P<metering_point_id>[-\w]+)/$','metering_point_view'),
    
    (r'^eventTypes','event_type_view'),
    (r'^eventType/(?P<event_type_id>[-\w]+)/$','event_type_view'),
    
    (r'^referenceConsumption','reference_consumption_view'),
    #(r'^goals','goal_view'),
    #(r'^goal/(?P<goal_id>[-\w]+)/$','goal_view'),
)

urlpatterns += patterns('sd_store.views.energy',
    # energy version
    (r'^energy/data', 'meter_reading_view', {'data_type': 'energy'}),
    
    (r'^energy/alwaysOn/','always_on_view', {'data_type': 'energy'}),
    (r'^energy/total/','total_energy_view'),

    (r'^energy/totalCost/','total_energy_cost_view'),
    
    # power version
    (r'^power/data', 'meter_reading_view', {'data_type': 'power'}),

    (r'^power/alwaysOn','always_on_view', {'data_type': 'power'}),

    # general
    (r'^eventNames','event_names_view'),
    (r'^events','event_view'),
    (r'^event/(?P<event_id>[-\w]+)/$','event_view'),
    (r'^event','event_view'),
    
    (r'^liveStats','live_stats_view'),
    (r'^savings','savings_view'),
)

urlpatterns += patterns('sd_store.views.external',
    (r'^powerNow','power_now_view'),
    (r'^update','update_view'),
    (r'^checkAlertMeLogin','check_alertme_login_view'),

# TODO: the following methods are not compatible with the protected_store setup
#    (r'^getEventLog','event_log_view'),
#    
#    (r'^smartPlugOn','smartplug_on_view'),
#    (r'^smartPlugOff','smartplug_off_view'),
#    
#    (r'^buttonFlashOn','button_flash_on_view'),
#    (r'^buttonFlashOff','button_flash_off_view'),
#    
#    (r'^smartPlugState','smart_plug_state_view'),
#    (r'^toggleSmartPlug','toggle_smart_plug_view'),   
#    
#    (r'^toggleUserBattery','toggle_user_battery_view'),  
)


