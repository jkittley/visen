#encoding:UTF-8

# 
#  THIS IS JUST CODE SCRAPS TO BUILD SETS OF GRAPHS AND 
#  HAS NO CORE FUNCTIONALITY
# 


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from sd_store.models import *
from frontend.models import *
from datetime import datetime, timedelta
from optparse import make_option
import time, os
from django.core.management import call_command

class Command(BaseCommand):

    def handle(self, *args, **options):
        
        # 
        # New Calendar Combo of whole year
        # 
        year = 2014
        seasons = get_season_dates(year)
        for site_type in ["depot","library","leisure"]:
            profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
            for profile in profiles:
                print "======================================================="
                print call_command('chart_calendar_vs_opening', 
                    period_str=str( datetime.strftime(seasons['winter']['start'], '%Y-%m-%d')+','+datetime.strftime(seasons['autumn']['end'], '%Y-%m-%d') ),
                    filename='zzz_images/chart_calendar_vs_opening/'+site_type+'/'+profile.longname+'.pdf',
                    sensor_name=profile.sensor.mac,
                )
                print "======================================================="


        # 
        # Boxplot of whole year
        # 
        # year = 2014
        # seasons = get_season_dates(year)
        # for channel_name in ['gas','electricity']:
        #     for site_type in ["depot","library","leisure"]:
        #         print "======================================================="
        #         print call_command('chart_boxplot_year', 
        #             year = year,
        #             filter=site_type,
        #             channel_name=channel_name,
        #             filename='zzz_images/chart_boxplot_year/'+channel_name+'/'+site_type+'.pdf',
        #             samescale=False,
        #         )
        #         print "======================================================="


        # 
        # Radar of usage for sample periods
        # 
        # year = 2014
        # seasons = get_season_dates(year)
        # for site_type in ["depot","library","leisure"]:
        #     for season in seasons:
        #         print "======================================================="
        #         print seasons[season]['start'], 'to', seasons[season]['end']
        #         print call_command('chart_radar_channel_vs_opening', 
        #             year = year,
        #             filter=site_type,
        #             filename='zzz_images/chart_radar_channel_vs_opening/'+season+'/'+site_type+'.png',
        #             period_str=str( datetime.strftime(seasons[season]['start'], '%Y-%m-%d')+','+datetime.strftime(seasons[season]['end'], '%Y-%m-%d') ),
        #             normalize = True,
        #             open_or_not = True
        #         )
        #         print "======================================================="



        # 
        # Time series of day usage for sample periods
        # 
        # for site_type in ["depot","library","leisure"]:
        #     profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
        #     for profile in profiles:
        #         print "======================================================="
        #         print call_command('chart_time_channel_vs_opening', 
        #             sensor_name=profile.sensor.mac,
        #             channel_list=['gas','electricity'],
        #             filename='zzz_images/sample_periods/'+site_type+'/'+profile.longname+'.png',
        #             period_list=[
        #                 '2014-01-12, 2014-01-18',
        #                 '2014-04-13, 2014-04-19',
        #                 '2014-07-13, 2014-07-19',
        #                 '2014-10-12, 2014-10-18',
        #             ],
        #             normalize = False
        #         )
        #         print "======================================================="