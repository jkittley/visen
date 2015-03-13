#encoding:UTF-8
# 
# Produces a set of boxplots for each site
#

import datetime, math, json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
from frontend.models import *
from dateutil.rrule import rrule, DAILY, MINUTELY
from matplotlib.dates import WeekdayLocator
from optparse import make_option
import matplotlib.gridspec as gridspec
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Generates a set of boxplots for each sensor'
    option_list = BaseCommand.option_list + (
            make_option('--sensor',
                    dest='sensor_name',
                    default=None,
                    help='A sensor (Site) name'),
            make_option('--file',
                    dest='filename',
                    default=None,
                    help='A filename where to save the plot'),
    )


    def handle(self, *args, **options):
        
        if options['sensor_name'] == None:
            print "Please specify a sensor (by name) using --sensor"
            return

        # Is the sensor name a number i.e. the MAC address
        try:
            int(options['sensor_name'])
            sensor_name_is_number = True
        except:
            sensor_name_is_number = False

        # Get the sensors of the site type
        try:
            if sensor_name_is_number:
                profile = Sensor_profile.objects.get(sensor__mac=options['sensor_name'])
            else:
                profile = Sensor_profile.objects.get(longname__icontains=options['sensor_name'])
        except Sensor_profile.DoesNotExist:
            print "Failed to find sensor:",options['sensor_name']
            return
        except Sensor_profile.MultipleObjectsReturned:
            print "Sensor name entered ("+options['sensor_name']+") did not return a unique sensor."
            return

    
        # Check for opening hour data
        example_working_day = []
        channel_open  = Channel.objects.all().get(name__icontains='Opening') 
        if channel_open not in profile.sensor.channels.all():
            print profile.longname, 'has no openning hour data'
        else:
            # Opening days
            readings_open = SensorReading.objects.filter(sensor=profile.sensor, timestamp__year=2013, channel=channel_open)
            for r in readings_open:
                key = r.timestamp.strftime('%Y-%m-%d')
                if r.value > 0:
                    example_working_day = [ key ]
                    break



        bankholidays = [
            '2013-12-25',
            '2013-12-26',
            '2014-01-01',
            '2014-04-18',
            '2014-04-21',
            '2014-05-05',
            '2014-05-26',
            '2014-08-25',
            '2014-12-25',
            '2014-12-26',
        ]

        # Call day patten creator
        print call_command('tier1_time_channel_vs_opening', 
            sensor_name=profile.sensor.mac,
            channel_list=['gas','electricity'],
            filename=options['filename'],
            date_list=example_working_day + bankholidays,
            normalize = False
        )
             
