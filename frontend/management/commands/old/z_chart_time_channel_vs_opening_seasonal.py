#encoding:UTF-8
# 
# Plot the daily patterns for a site. One time series per season
# Highlight the opening hours
# 
# 
# 

import datetime
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
        
        seasons = get_season_dates(2014)

        channel_gas  = Channel.objects.all().get(name='Gas')  
        channel_elec = Channel.objects.all().get(name='Electricity')  
        channel_open = Channel.objects.all().get(name__icontains='Opening') 

        for site_type in ["library","leisure"]:
            for channel in [channel_gas, channel_elec]:

                # Get all the sensors of the site type
                profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
              
                # Loop through each profile 
                for profile in profiles:

                    if channel not in profile.sensor.channels.all():
                        continue

                    print profile.sensor.mac + ' ' + profile.sensor.name

                    # Create plots 1 per season
                    fig, plots = plt.subplots(4)
                    fig.set_size_inches(100,15)
                
                    # For each season
                    season_count = 0
                    for season in ['winter','spring','summer','winter']:

                        print season 

                        # Process Data
                        start = seasons[season]['start']
                        end   = seasons[season]['end']
                        readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start, end), channel=channel)
                        open_hrs = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start, end), channel=channel_open)
            
                        data  = {}
                        ohrs  = {}
                        dates = []
                        xlab  = []
                        xtick = []

                        # Interval String
                        intstr = '%Y-%m-%d %H'
                        intmin = 60 #mins                    

                        # Build a list of dates
                        for d in rrule(MINUTELY, dtstart=start, until=end, interval=intmin):
                            dstring = d.strftime(intstr)
                            dates.append(d)
                            data[dstring] = 0
                            ohrs[dstring] = 0

                        prev_month = None
                        for d in rrule(DAILY, dtstart=start, until=end, interval=1):
                            xtick.append(d)
                            if prev_month == None or prev_month != d.month:
                                xlab.append(d.strftime('%d\n%b'))
                                prev_month = d.month
                            else:
                                xlab.append(d.strftime('%d'))
                                


                        # Work out total reading for day in month
                        for r in readings:
                            data[r.timestamp.strftime(intstr)] += r.value
                        data_vals = []    
                        for key in sorted(data):    
                            data_vals.append(data[key])


                        # Work out total number of hours open
                        for r in open_hrs:
                            if r.value > 0:
                                ohrs[r.timestamp.strftime(intstr)] = 1
                        ohrs_vals = []    
                        for key in sorted(ohrs):    
                            ohrs_vals.append(ohrs[key])

                            
                        x  = dates
                        y1 = np.array(data_vals)
                        y2 = np.array(ohrs_vals)

                        
                        ax1 = plots[season_count]
                        if season_count == 0:
                            ax1.set_title(season.capitalize()+' -- '+site_type.capitalize()+', '+channel.name.capitalize()+', '+profile.longname)
                        else:
                            ax1.set_title(season.capitalize())
                        
                        # Plot of usage
                        ax1.plot_date(x, y1, 'b-')
                        ax1.set_xlabel('')
                        ax1.set_ylabel(channel.name.capitalize()+' Usage', color='b')
                        for tl in ax1.get_yticklabels():
                            tl.set_color('b')

                        # X Labels
                        ax1.set_xticks(xtick)
                        ax1.set_xticklabels(xlab)
                        ax1.tick_params(axis='x', labelsize=10)

                        # Plot open hours
                        ax2 = ax1.twinx()
                        ax2.plot(x, y2, 'g-')
                        ax2.set_ylim([0., 1.0])
                        ax2.set_ylabel('Hours When Open', color='g')
                        for tl in ax2.get_yticklabels():
                            tl.set_color('g')
                        ax2.fill_between(x, 0, y2, facecolor='green', alpha=0.5)
                    

                        season_count += 1

                    # Save the Plot
                    plt.grid(True)
                   
                    filename = 'zzz_images/'+site_type.capitalize()+'_'+channel.name.capitalize()+'__'+profile.longname+'.png'
                    fig.savefig(filename, dpi=100)

                 
                    





        
  

