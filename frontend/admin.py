from django.contrib import admin
from frontend.models import *


admin.site.register(Chart)


class Sensor_profileAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'longname', 'address' , 'postcode', 'lon', 'lat')
    search_fields = ('longname','address' , 'postcode')

class VisInputline(admin.TabularInline):
    model = VisInput
    extra = 2

class VisualisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'chart')
    inlines = [VisInputline]


admin.site.register(Visualisation, VisualisationAdmin)
admin.site.register(Sensor_profile, Sensor_profileAdmin)