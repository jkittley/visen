from models import StudyInfo, Meter, SensorReading, MeteringPoint, Event, Goal,\
        EventType, Channel, Sensor, UserProfile
        #Booking, 

#import alertme

from django.contrib import admin

#from django.contrib.auth.admin import UserAdmin
#from django.contrib.auth.forms import UserCreationForm
#from django.utils.translation import ugettext_lazy as _
#from django import forms

#class AlertMeUserAdminForm(forms.ModelForm):
#    class Meta:
#        model = AlertMeUser
#    password = forms.CharField( help_text=_("Use '[algo]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."))


class StudyInfoInline(admin.StackedInline):
    model = StudyInfo
    extra = 0

#class AlertMeUserAdmin(UserAdmin):
#    
#    fieldsets = [
#        ('Essentials',          {'fields': ['username', 'password', 'alertme_password']}),
#        (_('Groups'), {'fields': ('groups',)}),
#        ('Name',                {'fields': ['first_name', 'last_name'], 'classes': ['collapse']}),
#        ('AlertMe settings',    {'fields': ['user_level', 'web_version', 'registration_date', 'energy_price', 'status', 'access', 'settings', 'swingometer_shared'], 'classes': ['collapse']}),
#        ('Preferences',            {'fields': ['language', 'currency', 'timezone', 'daylight_saving', 'temperature_format', 'date_format', 'time_format'], 'classes': ['collapse']}),
#        ('Sharing',             {'fields': ['fe_sharing', 'fe_allowed_users', 'facebook_sharing', 'facebook_allowed_users'], 'classes': ['collapse']}),
#    ]
#    
#    inlines = [StudyInfoInline]
#    form = AlertMeUserAdminForm
#    list_display = ('username', 'recent_data', 'no_events', 'control_group', 'baseline_consumption', 'start_date', 'last_login')

class MeterAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fields',            {'fields': ['mac', 'user', 'sensor_type', 'name', 'channels']}),
    ]
    list_display = ('name', 'user', 'mac')
    search_fields = ('user__username',)
    
class SensorAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fields',            {'fields': ['mac', 'user', 'sensor_type', 'name', 'channels']}),
    ]
    list_display = ('name', 'user', 'mac')
    search_fields = ('user__username',)
    
class SensorReadingAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fields',            {'fields': ['timestamp', 'sensor', 'value', 'channel']}),
    ]
    list_display = ('timestamp', 'sensor', 'channel', 'value')
    search_fields = ('sensor__user__username','channel__name')

class MeteringPointAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fields',            {'fields': ['name', 'description', 'sensor', 'user']}),
    ]
    
class EventTypeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fields',              {'fields': ['name', 'icon', 'alt_icon']}),
    ]
    
class EventAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fields',
         {
          'fields': ['event_type', 'name', 'description', 'sensor', 'start', 'end', 'metering_points']
          }),
    ]
    list_display = ('name', 'sensor', 'start', 'end')

class GoalAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fields',            {'fields': ['name', 'description', 'user', 'start', 'end', 'consumption']}),
    ]

class StudyInfoAdmin(admin.ModelAdmin):
    #fieldsets = [
    #    ('Fields',              {'fields': ['user', 'baseline_consumption', 'start_date']}),
    #]
    list_display = ('user', 'initial_credit', 'baseline_consumption', 'start_date') #, 'calculate_reward')

#class BookingAdmin(admin.ModelAdmin):
#    fieldsets = [
#        ('Fields',              {'fields': ['user', 'name', 'start', 'load', 'price', 'duration']}),
#    ]
#    list_display = ('user', 'name', 'start', 'duration', 'price', 'load')
    
#admin.site.register(AlertMeUser, AlertmeUserAdmin)
admin.site.register(Sensor, SensorAdmin)
admin.site.register(Meter, MeterAdmin)
admin.site.register(Channel)
admin.site.register(SensorReading, SensorReadingAdmin)
admin.site.register(MeteringPoint, MeteringPointAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Goal, GoalAdmin)
admin.site.register(EventType, EventTypeAdmin)

admin.site.register(StudyInfo, StudyInfoAdmin)
admin.site.register(UserProfile)
