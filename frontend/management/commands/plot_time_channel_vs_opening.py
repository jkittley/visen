#encoding:UTF-8
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

class Command(BaseCommand):
    
    def handle(self, *args, **options):



        years    = mdates.YearLocator()   # every year
        months   = mdates.MonthLocator()  # every month
        yearsFmt = mdates.DateFormatter('%Y')

        # load a numpy record array from yahoo csv data with fields date,
        # open, close, volume, adj_close from the mpl-data/example directory.
        # The record array stores python datetime.date as an object array in
        # the date column
        datafile = cbook.get_sample_data('goog.npy')
        r = np.load(datafile).view(np.recarray)

        fig, ax = plt.subplots()
        ax.plot(r.date, r.adj_close)


        # format the ticks
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)
        ax.xaxis.set_minor_locator(months)

        datemin = datetime.date(r.date.min().year, 1, 1)
        datemax = datetime.date(r.date.max().year+1, 1, 1)
        ax.set_xlim(datemin, datemax)

        # format the coords message box
        def price(x): return '$%1.2f'%x
        ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
        ax.format_ydata = price
        ax.grid(True)

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        fig.autofmt_xdate()

        plt.show()

        # --------------------------------------------------------------------------------
        #  Bar Chart - Dasys Of Month Total Usage
        # --------------------------------------------------------------------------------
        # year = 2014
        # maxcount = 2
        # counter  = 0
        # seasons = get_season_dates(year)
        # channel_gas  = Channel.objects.all().get(name='Gas')  
        # channel_elec = Channel.objects.all().get(name='Electricity')  
        # channel_open = Channel.objects.all().get(name__icontains='Opening') 

        # for site_type in ["depot","library","leisure"]:
        #     for channel in [channel_gas, channel_elec]:

        #         # Get all the sensors of the site type
        #         profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
        #         master = []
        #         labels = []

        #         # Loop through each profile 
        #         for profile in profiles:

        #             if channel not in profile.sensor.channels.all():
        #                 continue

        #             # Create plot
        #             fig = plt.figure(figsize=(14, 8))

        #             fig.suptitle(site_type.capitalize()+' '+channel.name.capitalize()+' '+profile.longname+' (Total Day Usage / Hours Open)' , fontsize=14, fontweight='bold')
                    
        #             fig.subplots_adjust(wspace=0.4, hspace=0.4)
       
        #             print profile.sensor.mac + ' ' + profile.sensor.name

        #             readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel)
        #             open_hrs = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel_open)

        #             data = {}
        #             ohrs = {}
        #             for i in range(1,13):
        #                 data[i] = { 'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0 }
        #                 ohrs[i] = { 'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0 }
                    
        #             # Work out total reading for day in month
        #             for r in readings:
        #                 data[int(r.timestamp.strftime('%m'))][r.timestamp.strftime('%a')] += r.value

        #             # Work out total number of hours open

        #             for o in open_hrs:
        #                 ohrs[int(o.timestamp.strftime('%m'))][o.timestamp.strftime('%a')] += (o.value * 0.5)
                      

        #             # Work out total reading / hours open
        #             for m in data:
        #                 for d in data[m]:
        #                     if ohrs[m][d] > 0:
        #                         data[m][d] = data[m][d] / ohrs[m][d]


        #             bottom=0
        #             width=10
        #             days   = [ 'Sun','Mon','Tue','Wed','Thu','Fri','Sat' ]
        #             months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
                    
        #             for month in data:
        #                 tmpdata = []
        #                 ax1 = None
        #                 ax1 = fig.add_subplot(2,6,month)
                        
        #                 for day in days:
        #                     tmpdata.append(data[month][day])
                        
        #                 cms = np.array(tmpdata)
        #                 ax1.set_title(months[month-1])
        #                 ax1.bar(range(0,7), cms, bottom=bottom)
        #                 ax1.set_xticklabels(days, rotation=90,  fontsize=10)  
        #                 ax1.tick_params(axis='y', labelsize=10)
                        
        #                 if month==1 or month==7:
        #                     ax1.set_ylabel('Total Readings This Day - This Month',  fontsize=10)
                    
        #             directory = 'zzz_images/bar/days_of_month_divided_by_opening/'
        #             filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+' '+profile.longname+'.png'
        #             if not os.path.exists(directory):
        #                 os.makedirs(directory)

        #             fig.savefig(directory+filename, bbox_inches='tight')
        #             plt.clf()

                





        
  

