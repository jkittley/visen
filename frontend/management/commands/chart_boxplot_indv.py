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
        
       

        # Load the channel
        try:
            channel  = Channel.objects.all().get(name=options['channel_name'])  
        except Channel.DoesNotExist:
            print "Channel does not exist", options['channel_name']
            return

        # Load the seasonal data
        seasons = get_season_dates(options['year'])

        # Get all the sensors of the site type
        profiles = Sensor_profile.objects.filter(longname__icontains=options['filter'])
        master  = {}
        highest = 0

        # Loop through each profile 
        for profile in profiles:

            if channel not in profile.sensor.channels.all():
                continue

            winter_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['winter']['end']), channel=channel)
            spring_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['spring']['start'], seasons['spring']['end']), channel=channel)
            summer_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['summer']['start'], seasons['summer']['end']), channel=channel)
            autumn_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['autumn']['start'], seasons['autumn']['end']), channel=channel)
            
            master[profile.sensor.mac] = {
                'profile': profile,
                'data': { 
                    'byday':  { 'Mon':[], 'Tue':[], 'Wed':[], 'Thu':[], 'Fri':[], 'Sat':[], 'Sun':[] },
                    'spring': { 'weekend':{}, 'weekday':{} },
                    'summer': { 'weekend':{}, 'weekday':{} },
                    'autumn': { 'weekend':{}, 'weekday':{} },
                    'winter': { 'weekend':{}, 'weekday':{} },
                }
            }

            # Package up all the readings in to the bins
            local_highest = -1
            for season_readings in [['winter',winter_readings], ['spring',spring_readings], ['summer',summer_readings], ['autumn',autumn_readings]]: 
                for r in season_readings[1]:
                    
                    if r.timestamp.isoweekday() >= 6:
                        daytype = 'weekend'
                    else:
                        daytype = 'weekday'
                    try:  
                        master[profile.sensor.mac]['data'][season_readings[0]][daytype][r.timestamp.strftime('%Y-%m-%d')].append(r.value)
                    except KeyError:
                        master[profile.sensor.mac]['data'][season_readings[0]][daytype][r.timestamp.strftime('%Y-%m-%d')] = [ r.value ]
                    
                    # By day
                    master[profile.sensor.mac]['data']['byday'][r.timestamp.strftime('%a')].append(r.value)

                    if r.value > highest:
                        highest = r.value
                    if r.value > local_highest:
                        local_highest = r.value


        # -- END OF PROFILE LOOP -----------------------

        number_cols = 1
        # number_rows = int( math.ceil( float( len(master) ) / float(number_cols) ) )
        number_rows = len(master)

        # print 'Master Length', len(master)
        # print 'No cols', number_cols
        # print 'No rows', number_rows

        # Create plots 
        fig = plt.figure(figsize=(8 * number_cols, 4 * number_rows))
        fig.suptitle(options['filter'].capitalize()+' '+channel.name.capitalize()+' -- '+seasons['winter']['start'].strftime('%Y-%m-%d')+' '+seasons['autumn']['end'].strftime('%Y-%m-%d'), fontsize=14, fontweight='bold')
        fig.subplots_adjust(wspace=0.2, hspace=0.4)
        
        plot_pos_count = 0

        for mac in master:

            print number_rows, number_cols, plot_pos_count

            ax1 = fig.add_subplot(number_rows, number_cols, plot_pos_count)
            
            if options['samescale']:
                plt.ylim([-0.5, highest])

            box_labels = []
            box_data   = []
            all_year   = []

            # Weekend / Weekday
            for season in ['winter','spring','summer','autumn']:
                for daytype in master[mac]['data'][season]:
                    tmp = master[mac]['data'][season][daytype].values()
                    box_data.append(tmp)
                    all_year = all_year + tmp
                    box_labels.append(season+'\n'+daytype)
            
            # Season totals
            for season in ['winter','spring','summer','autumn']:    
                box_data.append( master[mac]['data'][season]['weekend'].values() + master[mac]['data'][season]['weekday'].values() )
                box_labels.append(season)

            # Weekdays
            for dayname in ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']:  
                box_data.append( master[mac]['data']['byday'][dayname] )  
                box_labels.append(dayname)

            # Year
            box_data.append( all_year )
            box_labels.append('Year')

            # Build plot
            ax1.set_title(master[mac]['profile'].longname)
            box = ax1.boxplot(box_data, notch=True, patch_artist=True)
            ax1.set_xticklabels(box_labels, rotation=90, fontsize=10)  
            ax1.tick_params(axis='y', labelsize=10)

            # Color it
            for tl in ax1.get_xticklabels():
                if tl.get_text() == '':
                    continue
                elif 'weekend' in tl.get_text():
                    color = 'blue'
                elif 'weekday' in tl.get_text():
                    color = 'green'
                elif 'Year' in tl.get_text():
                    color = 'pink'
                elif tl.get_text().lower() in ['spring','summer','autumn','winter']:
                    color = 'tan'
                else:
                    color = 'orange'
                tl.set_color(color)
            
            colors = ['blue','green','blue','green', 'blue','green','blue','green', 'tan','tan','tan','tan', 'orange','orange','orange','orange','orange','orange','orange', 'pink']
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

                
                
