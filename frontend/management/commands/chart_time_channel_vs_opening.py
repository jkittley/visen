#encoding:UTF-8
# 
# Plot a days usage as a time series with an overlay of opening times
# 

import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import matplotlib.patches as mpatches
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
from frontend.models import *
from dateutil.rrule import rrule, DAILY, MINUTELY
from matplotlib.dates import WeekdayLocator
from optparse import make_option

class Command(BaseCommand):
    help = 'Generates a time series plot of sensor readings overlayed with opening hours'
    option_list = BaseCommand.option_list + (
        make_option('--sensor',
                    dest='sensor_name',
                    default=None,
                    help='A sensor (Site) name'),
        make_option('--channel',
                    action='append',
                    dest='channel_list',
                    default=None,
                    help='A list of channels to display'),
        make_option('--date',
                    action='append',
                    dest='date_list',
                    default=None,
                    help='A list of dates to display'),
        make_option('--file',
                    dest='filename',
                    default=None,
                    help='A filename where to save the plot'),
        make_option('--period',
                    action='append',
                    dest='period_list',
                    default=None,
                    help='A time period to display e.g. yyyy-mm-dd,yyyy-mm-dd'),
        make_option('--normalize',
                    action="store_true",
                    dest='normalize',
                    default=False,
                    help='Normalize the sensor readings (No value required)'),
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

        # Load default channel
        channel_open = Channel.objects.all().get(name__icontains='Opening') 

        # Inform user of sensor name being processed
        print "--------------------------------------------------------"
        print "Processing:           ", profile.longname

        # Loac all the channels from their models
        channels = []
        if options['channel_list']:
            for channel_name in options['channel_list']:
                try:
                    channels.append( Channel.objects.all().get(name__iexact=channel_name) )
                except Channel.DoesNotExist:
                    print "Failed to locate channel:", channel_name
                    return
                except Channel.MultipleObjectsReturned:
                    print "Channel name entered ("+channel_name+") did not return a unique channel."
                    return
        else:
            channels = list( profile.sensor.channels.all() )

        # Report channels being analysied
        print "With the channels:    ",channels

        # Process dates
        sample_periods = []
        if options['date_list']:
            for date_str in options['date_list']:
                try:
                   sample_periods.append( datetime.strptime(date_str,'%Y-%m-%d') )
                except ValueError:
                    print "Date invalid Format:", date_str, "Format should be yyyy-mm-dd"
                    return

        # Process periods
        if options['period_list']:
            for period_str in options['period_list']:
                try:
                    subset = period_str.split(',')
                    d1 = datetime.strptime(subset[0].strip(),'%Y-%m-%d')
                    d2 = datetime.strptime(subset[1].strip(),'%Y-%m-%d')
                    delta = d2 - d1
                    for i in range(delta.days + 1):
                        sample_periods.append(  d1 + timedelta(days=i) )
                except ValueError:
                    print "Date invalid Format:", period_str, "Format should be yyyy-mm-dd,yyyy-mm-dd"
                    return

        # Check if they entered any dates or periods
        if len(sample_periods) == 0:
            print "You must specify at least one date (--date yyyy-mm-dd) or time period (--period yyyy-mm-dd,yyyy-mm-dd)"
            return

        # Sort the days into order
        sample_periods.sort()

        # Dates to be displayed
        print "--------------------------------------------------------"
        print "Dates to be displayed:"
        for p in sample_periods:
            print p
        print "--------------------------------------------------------"

        # Check all channels use the same unit
        first_unit = None
        for channel in channels:
            if first_unit == None:
                first_unit = channel.unit
                continue
            if channel.unit != first_unit:
                print "All channels must use the same unit of messurement"
                print "First unit detected:", first_unit
                print "Failed for:", channel
                return

        # Get the max reading from all channels
        max_reading = 0
        for channel in channels:
            tmpmax = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(sample_periods[0], sample_periods[-1]), channel=channel).aggregate(Max('value'))
            if tmpmax['value__max'] > max_reading:
                max_reading = tmpmax['value__max']
        print 'Max reading:', max_reading

        # Create plots 1 per sample period
        fig, plots = plt.subplots(len(sample_periods))
        fig.set_size_inches(40, len(sample_periods) * 3 )
    
        # For each sample period
        sample_count = 0           
        for sample_period in sample_periods:
            print "Rendering:", sample_period 

            # Create the start and end time for each sample period
            start    = sample_period
            end      = sample_period + timedelta(days=1)

            # Get the opening hours data
            open_hrs = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start, end), channel=channel_open)

            # Init values
            data  = {}
            data_vals = {}
            ohrs  = {}
            dates = []
            xlab  = []
            xtick = []

            # Interval String
            intstr = '%Y-%m-%d %H:%M'
            intmin = 30 #mins                    

            # Build a list of datetimes and zero values
            for d in rrule(MINUTELY, dtstart=start, until=end, interval=intmin):
                dstring = d.strftime(intstr)
                # Create a list of datetimes for x scale
                dates.append(d)
                # Create a data dict for each channel and zero all values
                for channel in channels:
                    try:
                        data[channel][dstring] = 0
                    except:
                        data[channel] = {}
                        data[channel][dstring] = 0
                    data_vals[channel]     = []
                # Zero opening hour data
                ohrs[dstring] = 0

            # Build ticks for x labels
            for d in rrule(MINUTELY, dtstart=start, until=end, interval=30):
                xtick.append(d)
                xlab.append(d.strftime('%H:%M'))
              
            # For each channel process the readings into bins
            for channel in channels:
                local_max_reading = 0
                readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start, end), channel=channel)
                for r in readings:
                    if r.timestamp.minute == 59:
                        r.timestamp = r.timestamp + timedelta(minutes=1)
                    data[channel][r.timestamp.strftime(intstr)] += r.value  
                    if r.value > local_max_reading:
                        local_max_reading = r.value
                # Create a sorted list of values
                for key in sorted(data[channel]):    
                    if options['normalize']:
                        if local_max_reading != 0:
                            data_vals[channel].append(data[channel][key] / local_max_reading)
                        else: 
                            data_vals[channel].append(0)
                    else:
                        data_vals[channel].append(data[channel][key])

            # Work out total number of hours open
            for r in open_hrs:
                if r.value > 0:
                    ohrs[r.timestamp.strftime(intstr)] = 1
            ohrs_vals = []    
            for key in sorted(ohrs):    
                ohrs_vals.append(ohrs[key])

            # Basic scales for all plots
            x  = dates
            y2 = np.array(ohrs_vals)

            # Assign ax1 to current plot
            if len(sample_periods) == 1:
                ax1 = plots
            else:
                ax1 = plots[sample_count]

            # Only show sensor name of first plot
            if sample_count == 0:
                title  = sample_period.strftime('%B %d %Y (%A)')
                title += ' -- '+profile.longname+' -- '
                for channel in channels:
                    title += channel.name.capitalize()+' '
                ax1.set_title(title)
            else:
                ax1.set_title(sample_period.strftime('%B %d %Y (%A)'))
            
            # Plot of usage 
            colors = ['b','r','g','c','m','y','k']
            counter = 0
            for ch in data_vals: 
                ax1.step(x, data_vals[ch], colors[counter], label=ch.name)
                counter += 1

            ax1.set_xlabel('')
            ax1.set_ylabel(channel.name.capitalize()+' Usage', color='b')
            for tl in ax1.get_yticklabels():
                tl.set_color('b')

            # X Labels
            ax1.set_xticks(xtick)
            ax1.set_xticklabels(xlab)
            ax1.tick_params(axis='x', labelsize=10)
            ax1.set_ylim(bottom=0)

            # Set y scale
            if options['normalize']:
                ax1.set_ylim(ymax=1)
            else:
                ax1.set_ylim(ymax=max_reading)

            # Plot open hours
            ax2 = ax1.twinx()
            ax2.step(x, y2, 'g-')
            ax2.set_ylim([0., 1.0])
            ax2.set_ylabel('Hours When Open', color='g', visible=False)
            ax2.set_yticklabels([0,1], visible=False)
            for start, end in customFilter(y2):
                mask = np.zeros_like(y2)
                mask[start: end] = 1
                ax2.fill_between(x, 0, 1, where=mask, facecolor='green', alpha=0.5)
    
            # Show legend
            green_patch = mpatches.Patch(color='green', label='Opening Hrs')
            handles1, labels1 = ax1.get_legend_handles_labels()
            ax1.legend(handles1 + [green_patch], labels1 + ['Opening Hrs'])
  

            # Increment sample counter
            sample_count += 1


        # Add a grid
        plt.grid(True)
        
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
        



# Custom filter used to build the opening hour overlays
def customFilter(s):
    foundStart = False
    for i, val in enumerate(s):
        if not foundStart and val == 1:
            foundStart = True
            start = i-1
        if foundStart and val == 0:
            end = i-1
            yield (start, end+1)
            foundStart = False
    if foundStart:
        yield (start, len(s))  


  

