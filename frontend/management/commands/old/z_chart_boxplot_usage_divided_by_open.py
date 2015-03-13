#encoding:UTF-8
# 
# chart_boxplot_usage_divided_by_open
# 
# Use the same scale for each plot
# 
SAME_SCALE = True
# 
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

class Command(BaseCommand):
    
    def handle(self, *args, **options):
          
        year = 2014
        seasons = get_season_dates(year)
        channel_gas  = Channel.objects.all().get(name='Gas')  
        channel_elec = Channel.objects.all().get(name='Electricity')  
        channel_open = Channel.objects.all().get(name__icontains='Opening') 

        for site_type in ["library","leisure","depot"]:
            for channel in [channel_gas, channel_elec]:

                # Get all the sensors of the site type
                profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
                master  = {}
                highest = 0

                # Loop through each profile 
                for profile in profiles:

                    if channel not in profile.sensor.channels.all():
                        continue

                    print profile.sensor.mac + ' ' + profile.sensor.name

                    readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel)
                    open_hrs = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel_open)
                    
                    total_reading = {}
                    for r in readings:
                        total_reading += r.value

                    total_opening = {}
                    for r in open_hrs:
                        total_opening += r.value

                    master[profile.sensor.mac] = total_reading / total_opening


                # -- END OF PROFILE LOOP -----------------------

                number_cols = 2
                number_rows = int( math.ceil( float( len(master) ) / float(number_cols) ) )
                
                print 'Master Length', len(master)
                print 'No cols', number_cols
                print 'No rows', number_rows

                # Create plots 
                fig = plt.figure(figsize=(8 * number_cols, 4 * number_rows))
                fig.suptitle(site_type.capitalize()+' '+channel.name.capitalize()+' -- '+seasons['winter']['start'].strftime('%Y-%m-%d')+' '+seasons['autumn']['end'].strftime('%Y-%m-%d'), fontsize=14, fontweight='bold')
                fig.subplots_adjust(wspace=0.2, hspace=0.4)
                
                plot_pos_count = 0

        
                for mac in master:

                    print number_rows, number_cols, plot_pos_count

                    ax1 = fig.add_subplot(number_rows, number_cols, plot_pos_count)
                    
                    # Build plot
                    box_data = master.values()

                    # ax1.set_title(master[mac]['profile'].longname)
                    box = ax1.boxplot(box_data, notch=True, patch_artist=True)
                    ax1.set_xticklabels(['--'], rotation=90, fontsize=10)  
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
                        else:
                            color = 'tan'
                        tl.set_color(color)
                    
                    colors = ['blue','green','blue','green', 'blue','green','blue','green', 'tan','tan','tan','tan', 'pink']
                    for patch, color in zip(box['boxes'], colors):
                        patch.set_facecolor(color)

                    plot_pos_count += 1
                     

                # Save the plot
                directory = 'zzz_images/box/chart_boxplot_usage_divided_by_open/'
                filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+'.png'
                if not os.path.exists(directory):
                    os.makedirs(directory)
                fig.savefig(directory+filename, bbox_inches='tight')

                plt.clf()

                
                
