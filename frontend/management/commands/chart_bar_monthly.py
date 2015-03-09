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
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
from frontend.models import *
from dateutil.rrule import rrule, DAILY, MINUTELY
from matplotlib.dates import WeekdayLocator
from optparse import make_option

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

        # Load readings
        readings_gas  = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_gas)
        readings_elec = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_elec)
        readings_open = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_open)

        # Init vars
        mgas    = {}
        melec   = {}
        mopen   = {}
        
        current_month = start_week.month
        while current_month <= end.month
        print current_month
            mgas.append([0,0,0,0,0,0,0])
            melec.append([0,0,0,0,0,0,0])
            mopen.append([0,0,0,0,0,0,0])
            mtemp.append([0,0,0,0,0,0,0])
            current_date += timedelta()

        return 

        
        # Work out total reading for day in month
        for r in readings_gas:
            weeks_from_start_date = int ( math.floor( (r.timestamp - start_week).days / 7 ) )
            
            day_of_week = int(r.timestamp.strftime('%w'))
            mgas[month_num][day_of_week] += r.value

        # Work out total reading for day in month
        for r in readings_elec:
            month_num   = int(r.timestamp.strftime('%m'))
            day_of_week = int(r.timestamp.strftime('%w'))
            melec[month_num][day_of_week] += r.value

        # Work out total reading for day in month
        for r in readings_elec:
            month_num   = int(r.timestamp.strftime('%m'))
            day_of_week = int(r.timestamp.strftime('%w'))
            mopen[month_num][day_of_week] += (r.value * 0.5)









        # Create plot
        fig = plt.figure(figsize=(16, 8))

        # Title
        t = profile.longname + ' - Daily Totals per Month'
        if options['normalize']:
            t += ' - Divided by opening hours'
        if options['remove_closed_days']:
            t += ' - Closed days removed'

        fig.suptitle(t, fontsize=14, fontweight='bold')
        fig.subplots_adjust(wspace=0.4, hspace=0.4)

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



                

                 
                    





        
  

