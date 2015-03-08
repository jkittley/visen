#encoding:UTF-8
# 
# Look at each month in a year (of seasons Dec - Nov). 
# Add up all the readings for each day i.e. Mon, Tue, Wed, Thu, Fri, Sat, Sun
# and present as a bar graph.
# 
# Colour code each bar to indicate if a building is open or closed on that day
# 
# DIVIDE_BY_HOURS_OPEN: This flag sets wheather to divide each days readings by
# its opening hours
# 
DIVIDE_BY_HOURS_OPEN = False
# 
# REMOVE_CLOSED_DAYS: Hide the days where the site is closed
# 
REMOVE_CLOSED_DAYS   = False
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
        
        year = 2014
        maxcount = 2
        counter  = 0
        seasons = get_season_dates(year)
        channel_gas  = Channel.objects.all().get(name='Gas')  
        channel_elec = Channel.objects.all().get(name='Electricity')  
        channel_open = Channel.objects.all().get(name__icontains='Opening') 

        for site_type in ["library","leisure"]:
            for channel in [channel_gas, channel_elec]:

                # Get all the sensors of the site type
                profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
                master = []
                labels = []

                # Loop through each profile 
                for profile in profiles:

                    if channel not in profile.sensor.channels.all():
                        continue

                    # Create plot
                    fig = plt.figure(figsize=(16, 8))

                    t = site_type.capitalize()+' '+channel.name.capitalize()+' '+profile.longname + ' - Daily Totals per Month'
                    if DIVIDE_BY_HOURS_OPEN:
                        t += ' - Divided by opening hours'
                    if REMOVE_CLOSED_DAYS:
                        t += ' - Closed days removed'

                    fig.suptitle(t, fontsize=14, fontweight='bold')
                    
                    fig.subplots_adjust(wspace=0.4, hspace=0.4)
       
                    print profile.sensor.mac + ' ' + profile.sensor.name

                    readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel)
                    open_hrs = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel_open)

                    data = {}
                    ohrs = {}
                    for i in range(1,13):
                        data[i] = { 'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0 }
                        ohrs[i] = { 'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0 }
                    
                    # Work out total reading for day in month
                    for r in readings:
                        data[int(r.timestamp.strftime('%m'))][r.timestamp.strftime('%a')] += r.value

                    # Work out total number of hours open
                    for o in open_hrs:
                        ohrs[int(o.timestamp.strftime('%m'))][o.timestamp.strftime('%a')] += (o.value * 0.5)
                    
                    # 
                    if DIVIDE_BY_HOURS_OPEN:
                        for m in data:
                            for d in data[m]:
                                if ohrs[m][d] > 0:
                                    data[m][d] = data[m][d] / ohrs[m][d]
                    
                    # 
                    if REMOVE_CLOSED_DAYS:
                        for m in data:
                            for d in data[m]:
                                if ohrs[m][d] == 0:
                                    data[m][d] = 0


                    bottom = 0
                    width  = 10
                    days   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
                    months = ['Jan '+str(year),'Feb '+str(year),'Mar '+str(year),'Apr '+str(year),'May '+str(year),'Jun '+str(year),'Jul '+str(year),'Aug '+str(year),'Sep '+str(year),'Oct '+str(year),'Nov '+str(year),'Dec '+str(year-1)]
                    
                    plot_pos_count = 1
                    for month in [12,1,2,3,4,5,6,7,8,9,10,11]:
                        
                        tmpdata = []
                        ax1 = None
                        ax1 = fig.add_subplot(2,6,plot_pos_count)
                        plt.xlim([-0.5, 7])

                        for day in days:
                            tmpdata.append(data[month][day])
                                                
                        ax1.set_title(months[month-1])
                        barlist = ax1.bar(range(0,7), tmpdata, bottom=bottom, align='center')
                        ax1.set_xticklabels(['']+days, rotation=90,  fontsize=10)  
                        ax1.tick_params(axis='y', labelsize=10)
                        
                        counter = 0;
                        for tl in ax1.get_xticklabels():
                            if tl.get_text() != '':
                                if ohrs[month][tl.get_text()] > 0:
                                    tl.set_color('g')
                                    barlist[counter].set_color('g')
                                if REMOVE_CLOSED_DAYS and ohrs[month][tl.get_text()] == 0:
                                    tl.set_color('r')
                               
                                counter += 1


                        if plot_pos_count==1 or plot_pos_count==7:
                            ax1.set_ylabel('Total Readings This Day - This Month',  fontsize=10)
                            ax1.set_xlabel('Green = Open\nRed = Removed',  fontsize=10)
                        
                        plot_pos_count += 1

                    # Build directory path
                    directory = 'zzz_images/bar/days_of_month_coded_by_opening_days/'
                    if DIVIDE_BY_HOURS_OPEN:
                        directory += 'divided_by_opening_hours/'
                    else:
                        directory += 'normal/'
                    if REMOVE_CLOSED_DAYS:
                        directory += 'closed_days_removed/'
                    directory += site_type+'/'

                    # Save file
                    filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+' '+profile.longname+'.png'
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    fig.savefig(directory+filename, bbox_inches='tight')
                    plt.clf()



                

                 
                    





        
  

