#encoding:UTF-8
# 
# Produce a Radar diagram for each site.
# Each radar shows the opening hours, gas and electric for the period specified
# 
# 

import os
import datetime, math, json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from numpy.random import rand
from matplotlib.spines import Spine
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
import matplotlib.gridspec as gridspec

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
from frontend.models import *
from dateutil.rrule import rrule, DAILY, MINUTELY
from matplotlib.dates import WeekdayLocator
from sklearn.preprocessing import normalize

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
            make_option('--open_or_not',
                    action="store_true",
                    dest='open_or_not',
                    default=False,
                    help='If used opening times will be reduced to open or closed instead of number of hours'),
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
  
        # Get the channels
        channel_gas = Channel.objects.get(name__iexact='gas')
        channel_elec = Channel.objects.get(name__iexact='Electricity')
        channel_open = Channel.objects.all().get(name__icontains='Opening')
        channel_temp = Channel.objects.all().get(name__icontains='Temp') 

        # Get all readings
        readings_gas     = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_gas)
        readings_elec    = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_elec)
        readings_opening = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_open)
        readings_temp    = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start,end), channel=channel_temp)
        
        # Setup blank (and full) vals
        delta = end - start
        mgas    = []
        melec   = []
        mopen   = []
        mtemp   = []
        xlabels = []
        xlabels_sm = []
        ylabels = ['Sat','Fir','Thu','Wed','Tue','Mon','Sun']
        xticks  = []
        totals  = {}
        counter = 0
     
        for i in range(0, delta.days+1+int(start.strftime('%w')), 7):
            current_date = start_week + timedelta(days=i)
            mgas.append([-1,-1,-1,-1,-1,-1,-1])
            melec.append([-1,-1,-1,-1,-1,-1,-1])
            mopen.append([-1,-1,-1,-1,-1,-1,-1])
            mtemp.append([-50,-50,-50,-50,-50,-50,-50])
            xticks.append(i - 0.5)
            xlabels.append(current_date.strftime('%Y-%m-%d'))
            xlabels_sm.append('|')


        # Compile elec readings
        for r in readings_elec:
            weeks_from_start_date = int ( math.floor( (r.timestamp - start_week).days / 7 ) )
            day_of_week  = int(r.timestamp.strftime('%w'))
            if melec[weeks_from_start_date][day_of_week] == -1:
                melec[weeks_from_start_date][day_of_week] = r.value
            else:
                melec[weeks_from_start_date][day_of_week] += r.value
         
        # Compile gas readings
        for r in readings_gas:
            weeks_from_start_date = int ( math.floor( (r.timestamp - start_week).days / 7 ) )
            day_of_week  = int(r.timestamp.strftime('%w'))
            if mgas[weeks_from_start_date][day_of_week] == -1:
                mgas[weeks_from_start_date][day_of_week]  = r.value
            else:
                mgas[weeks_from_start_date][day_of_week] += r.value
            
        # Compile opening hours
        for r in readings_opening:
            weeks_from_start_date = int ( math.floor( (r.timestamp - start_week).days / 7 ) )
            day_of_week  = int(r.timestamp.strftime('%w'))
            if mopen[weeks_from_start_date][day_of_week] == -1:
                mopen[weeks_from_start_date][day_of_week] = (r.value * 0.5)
            else:
                mopen[weeks_from_start_date][day_of_week] += (r.value * 0.5)
          
        # Compile temperature
        for r in readings_temp:
            weeks_from_start_date = int ( math.floor( (r.timestamp - start_week).days / 7 ) )
            day_of_week  = int(r.timestamp.strftime('%w'))
            if mtemp[weeks_from_start_date][day_of_week] == -50:
                mtemp[weeks_from_start_date][day_of_week] = r.value
            else:
                mtemp[weeks_from_start_date][day_of_week] += r.value
                mtemp[weeks_from_start_date][day_of_week] = mtemp[weeks_from_start_date][day_of_week] / 2
        
    

        # -------------------------------------------------------------------------

        fig = plt.figure(figsize = (11,5.7))
        gs1 = gridspec.GridSpec(4, 1)
        gs1.update(wspace=0.025, hspace=0) # set the spacing between axes. 
        plt.gcf().subplots_adjust(bottom=0.2)

        # -------------------------------------------------------------------------

        # Rotate the array
        data = np.array(melec)
        data = np.ma.masked_array(data, data < 0)
        data = np.rot90(data, 1)
        mgas  = np.ma.masked_array(np.array(mgas),  np.array(mgas)  < 0)

        # Create the plot
        ax0 = plt.subplot(gs1[0])

        ax0.set_title(profile.sensor.mac+' '+profile.longname)

        # Set the y labels
        ax0.set_yticks([0.5,1.5,2.5,3.5,4.5,5.5,6.5])
        ax0.set_yticklabels(ylabels, va='center')
        ax0.tick_params(axis='y', labelsize=8)

        # Set the x labels
        ax0.set_xticks(np.arange( data.shape[1])+0.5, minor=False)
        ax0.set_xticklabels(xlabels_sm)
        ax0.tick_params(axis='x', labelsize=8)
        ax0.set_aspect('equal')

        # Limit the x scale so it looks neat
        plt.xlim(0, (delta.days + 8) / 7)

        # Build the mesh plot
        p = ax0.pcolormesh(data)
        c = plt.colorbar(p, shrink=0.9, aspect=10, fraction=.12, pad=.02)
        c.ax.tick_params(labelsize=8) 

        # Add a title
        ax0.set_ylabel(channel_elec.name.capitalize()+' ('+channel_gas.unit+')', fontsize=8)

        # -------------------------------------------------------------------------

        # Rotate the array
        data = np.array(mgas)
        data = np.ma.masked_array(data, data < 0)
        data = np.rot90(data, 1)

        # Create the plot
        ax1 = plt.subplot(gs1[1])

        # Set the y labels
        ax1.set_yticks([0.5,1.5,2.5,3.5,4.5,5.5,6.5])
        ax1.set_yticklabels(ylabels, va='center')
        ax1.tick_params(axis='y', labelsize=8)

        # Set the x labels
        ax1.set_xticks(np.arange( data.shape[1])+0.5, minor=False)
        ax1.set_xticklabels(xlabels_sm)
        ax1.tick_params(axis='x', labelsize=8)
        ax1.set_aspect('equal')

        # Limit the x scale so it looks neat
        plt.xlim(0, (delta.days + 8) / 7)

        # Build the mesh plot
        p = ax1.pcolormesh(data)
        c = plt.colorbar(p, shrink=0.9, aspect=10, fraction=.12, pad=.02)
        c.ax.tick_params(labelsize=8) 
       
        # Add a title
        ax1.set_ylabel(channel_gas.name.capitalize()+' ('+channel_gas.unit+')', fontsize=8)

        # -------------------------------------------------------------------------

        # Rotate the array
        data = np.array(mopen)
        data = np.ma.masked_array(data, data < 0)
        data = np.rot90(data, 1)

        # Create the plot
        ax2 = plt.subplot(gs1[2])

        # Set the y labels
        ax2.set_yticks([0.5,1.5,2.5,3.5,4.5,5.5,6.5])
        ax2.set_yticklabels(ylabels, va='center')
        ax2.tick_params(axis='y', labelsize=8)

        # Set the x labels
        ax2.set_xticks(np.arange( data.shape[1])+0.5, minor=False)
        ax2.set_xticklabels(xlabels_sm)
        ax2.tick_params(axis='x', labelsize=8)
        ax2.set_aspect('equal')

        # Limit the x scale so it looks neat
        plt.xlim(0, (delta.days + 8) / 7)

        # Build the mesh plot
        p = ax2.pcolormesh(data)
        c = plt.colorbar(p, shrink=0.9, aspect=10, fraction=.12, pad=.02)
        c.ax.tick_params(labelsize=8) 

        # Add a title
        ax2.set_ylabel('Opening\nhours (hours)', fontsize=8)
       
        # -------------------------------------------------------------------------

        # Rotate the array
        data = np.array(mtemp)
        data = np.ma.masked_array(data, data < -49)
        data = np.rot90(data, 1)

        # Create the plot
        ax3 = plt.subplot(gs1[3])

        # Set the y labels
        ax3.set_yticks([0.5,1.5,2.5,3.5,4.5,5.5,6.5])
        ax3.set_yticklabels(ylabels, va='center')
        ax3.tick_params(axis='y', labelsize=8)

        # Set the x labels
        ax3.set_xticks(np.arange( data.shape[1])+0.5, minor=False)
        ax3.set_xticklabels(xlabels, rotation=90)
        ax3.tick_params(axis='x', labelsize=8)
        ax3.set_aspect('equal')

        # Limit the x scale so it looks neat
        plt.xlim(0, (delta.days + 8) / 7)

        # Build the mesh plot
        p = ax3.pcolormesh(data)
        c = plt.colorbar(p, shrink=0.9, aspect=10, fraction=.12, pad=.02)
        c.ax.tick_params(labelsize=8) 

        # Add a title
        ax3.set_ylabel('Outside\ntemperature (^C)', fontsize=8)
        ax3.set_xlabel('Date of week beginning (Sunday) - [ Winter=Blue Green=Spring Red=Summer Orange=Autumn ]', fontsize=8)
        
        seasons = get_season_dates(2014)
        for tl in ax3.get_xticklabels():
            dt = datetime.strptime(tl.get_text(),'%Y-%m-%d') 
            season_colors = {
                'winter': 'blue',
                'spring': 'green',
                'summer': 'red',
                'autumn': 'orange',
            }
            for season in seasons:
                if dt >= seasons[season]['start'] and dt <= seasons[season]['end']:
                    tl.set_color(season_colors[season])


        # -------------------------------------------------------------------------

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
            plt.savefig(filename, dpi=200)

        



        
                
                
