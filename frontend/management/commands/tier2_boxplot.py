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

class Command(BaseCommand):
    help = 'Generates a set of boxplots for each sensor'
    option_list = BaseCommand.option_list + (
            make_option('--sensor',
                    dest='sensor_name',
                    default=None,
                    help='A sensor (Site) name'),
            make_option('--period',
                    dest='period_str',
                    default=None,
                    help='A time period to display e.g. yyyy-mm-dd,yyyy-mm-dd'),
            make_option('--file',
                    dest='filename',
                    default=None,
                    help='A filename where to save the plot'),
    )


    def handle(self, *args, **options):
        
        if options['sensor_name'] == None:
            print "Please specify a sensor (by name) using --sensor"
            return

        if options['period_str'] == None:
            print "Please specify a period using --period"
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

        # Load the channels
        channel_gas  = Channel.objects.get(name__iexact='gas')
        channel_elec = Channel.objects.get(name__iexact='Electricity')
        channel_open = Channel.objects.all().get(name__icontains='Opening') 

        # Fetch the readings  
        readings = {}
        readings[channel_gas]   = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_gas)
        readings[channel_elec]  = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_elec)
        readings_open           = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_open)

        # Init vars
        master = { 'opendays': [0,0,0,0,0,0,0] } 
        
        # Work out if open on days
        for r in readings_open:
            if r.value > 0:
                master['opendays'][int(r.timestamp.strftime('%w'))] = 1

        # Process the readings
        for channel in [channel_gas, channel_elec]:
            master[channel] = {
                'whole'    : [],
                'byday'    : [[],[],[],[],[],[],[]],
                'opendays' : [0,0,0,0,0,0,0],
                'byseason' : { 'winter':[], 'spring':[], 'summer':[], 'autumn':[] }
            }
            # Process usage readings
            for r in readings[channel]:
                master[channel]['whole'].append(r.value)
                master[channel]['byday'][int(r.timestamp.strftime('%w'))].append(r.value) 
                seasons = get_season_dates(2014)
                for season in seasons:
                    if r.timestamp >= seasons[season]['start'] and r.timestamp <= seasons[season]['end']:
                        master[channel]['byseason'][season].append(r.value)
           


        # Create plots 
        fig = plt.figure(figsize=(8, 5))
        gs1 = gridspec.GridSpec(2, 1)
        gs1.update(wspace=0.025, hspace=0.1)
        fig.suptitle(profile.sensor.mac+' '+profile.longname, fontsize=14, fontweight='bold')
        fig.subplots_adjust(wspace=0.2, hspace=0.4)
        plt.gcf().subplots_adjust(bottom=0.2)


        plot_pos_count = 1
        for channel in [channel_gas, channel_elec]:

            ax1 = fig.add_subplot(gs1[plot_pos_count-1])

            box_labels = []
            box_data   = []
            all_year   = []

            # Season totals
            for season in ['winter','spring','summer','autumn']:    
                box_data.append( master[channel]['byseason'][season] )
                box_labels.append(season)

            # Weekdays
            daynames = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
            for daynum in [0,1,2,3,4,5,6]:  
                box_data.append( master[channel]['byday'][daynum] )  
                tmp_label = daynames[daynum]
                if master['opendays'][daynum] == 1:
                    tmp_label += ' (Open)'
                box_labels.append(tmp_label)

            # Year
            box_data.append( master[channel]['whole'] )
            box_labels.append('All')

            # Build plot
            box = ax1.boxplot(box_data, notch=True, patch_artist=True)
            if plot_pos_count != 1:
                ax1.set_xticklabels(box_labels, rotation=90, fontsize=10)  
            else:
                ax1.get_xaxis().set_visible(False)
            
            ax1.set_ylabel(channel.name.capitalize()+' usage ('+channel.unit+')', fontsize=8)
            ax1.tick_params(axis='y', labelsize=10)
            


            colors = ['blue','green','red','orange', 'brown','tan','tan','tan','tan','tan','brown','pink']
            for patch, color in zip(box['boxes'], colors):
                patch.set_facecolor(color)

            plot_pos_count += 1
             

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

                
                
