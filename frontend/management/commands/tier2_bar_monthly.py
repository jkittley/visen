#encoding:UTF-8
# 
# Look at each month in a year (of seasons Dec - Nov). 
# Add up all the readings for each day i.e. Mon, Tue, Wed, Thu, Fri, Sat, Sun
# and present as a bar graph.
# 
# Colour code each bar to indicate if a building is open or closed on that day
# 

import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import os, math
from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
from frontend.models import *
from dateutil.rrule import rrule, DAILY, MINUTELY
from matplotlib.dates import WeekdayLocator
from optparse import make_option
import matplotlib.gridspec as gridspec

class Command(BaseCommand):
    help = 'Produce a Radar diagram for each sensors gas and electricity channels, then overlayed with opening hours'
    option_list = BaseCommand.option_list + (
            make_option('--period',
                    dest='period_str',
                    default=None,
                    help='A time period to display e.g. yyyy-mm-dd,yyyy-mm-dd'),
            make_option('--sensor',
                    dest='sensor_name',
                    default=None,
                    help='A sensor (Site) name'),
            make_option('--file',
                    dest='filename',
                    default=None,
                    help='A filename where to save the plot'),
            make_option('--normalize',
                    action="store_true",
                    dest='normalize',
                    default=False,
                    help='Normalize the sensor readings (No value required)'),
            make_option('--remove_closed_days',
                    action="store_true",
                    dest='remove_closed_days',
                    default=False,
                    help='If used days on which the site is closed will be removed'),
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

        # Load channels
        channel_gas  = Channel.objects.all().get(name='Gas')  
        channel_elec = Channel.objects.all().get(name='Electricity')  
        channel_open = Channel.objects.all().get(name__icontains='Opening') 

        # Process periods
        try:
            subset = options['period_str'].split(',')
            start = datetime.strptime(subset[0].strip(),'%Y-%m-%d')
            end   = datetime.strptime(subset[1].strip(),'%Y-%m-%d')
            start_week = start - timedelta(days=int(start.strftime('%w')))
        except:
            print "Date invalid Format:", options['period_str'], "Format should be yyyy-mm-dd,yyyy-mm-dd"
            return

        # Check if they entered any dates or periods
        if start > end:
            print "The period must no end before it starts"
            return

    
        # Init vars
        master      = {}
        opening     = None
        number_cols = 0
        number_rows = 0
        max_reading = 0

        # Check for opening hour data
        if channel_open not in profile.sensor.channels.all():
            print profile.longname, 'has no openning hour data'
        else:
            # Opening days
            opening     = {}
            readings_open = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_open)
            for r in readings_open:
                key = r.timestamp.strftime('%Y-%m')
                day = int( r.timestamp.strftime('%w') )
                if key not in opening:
                    opening[key]  = [0,0,0,0,0,0,0]
                if r.value > 0:
                    opening[key][day] = 1

        # Build channel list
        channels = []
        if channel_elec in profile.sensor.channels.all():
            channels.append(channel_elec)
        if channel_gas in profile.sensor.channels.all():
            channels.append(channel_gas)
        
        if len(channels) == 0:
            print profile.longname, 'has no channels'
            return

        # Process
        for channel in channels:  
            readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel)
            for r in readings:
                key = r.timestamp.strftime('%Y-%m')
                day = int( r.timestamp.strftime('%w') )
                if channel not in  master:
                    master[channel] = {}
                if key not in master[channel]:
                    master[channel][key] = [0,0,0,0,0,0,0]
                master[channel][key][day] += r.value
                
                # Max reading
                if master[channel][key][day] > max_reading:
                    max_reading = master[channel][key][day]
                
            # Calc the number of row columns
            if channel in master:
                if len(master[channel]) > number_cols:
                    number_cols = len(master[channel])  

            number_rows += 1
        
        if number_cols == 0:
            print 'No columns to print'
            return
        if number_rows == 0:
            print 'No rows to print'
            return


        # Plot    
        fig = plt.figure(figsize=(2 * number_cols, 2 + (3 * number_rows)))
        gs1 = gridspec.GridSpec(number_rows, number_cols)
        gs1.update(wspace=0.8, hspace=0.5)
        fig.suptitle(profile.longname+' (O) in day name = known to be open (same cannot be said for closed)', fontsize=12, fontweight='bold')
        plt.gcf().subplots_adjust(bottom=0.2)
        
        i = 1
        for channel in master:
            for month in sorted(master[channel]):
                ax = fig.add_subplot(gs1[i-1])
                # bar graphs
                width = 0.8
                ax.bar(np.arange(7), master[channel][month])
                ax.set_title(month, fontsize=10)
                ax.set_xticks(range(0,8))

                # Build labels
                tmp_label = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
                if opening:
                    for op in range(0,7):
                        if opening[month][op] == 1:
                            tmp_label[op] += ' (O)'
                ax.set_xticklabels(tmp_label, rotation=90)
                
                ax.tick_params(axis='x', labelsize=8)
                ax.tick_params(axis='y', labelsize=8)
                ax.set_ylabel(channel.name, fontsize=10)
                if options['normalize']:
                    ax.set_ylim(0, max_reading)
                i+=1

        # Show / Save the Plot
        if options['filename']==None:
            print "Displaying"
            plt.show()
        else:
            filename  = options['filename']
            directory = os.path.dirname(filename)
            if not os.path.exists(directory):
                os.makedirs(directory)
            print "Saving to:", filename 
            fig.savefig(filename, dpi=100)

        plt.clf()