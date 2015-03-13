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
from matplotlib.spines import Spine
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
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
                    dest='sensor_list',
                    action="append",
                    default=None,
                    help='A sensor to add to the visualisation'),
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

        # Process periods
        sample_period = []
        try:
            subset = options['period_str'].split(',')
            start = datetime.strptime(subset[0].strip(),'%Y-%m-%d')
            end   = datetime.strptime(subset[1].strip(),'%Y-%m-%d')
        except:
            print "Date invalid Format:", options['period_str'], "Format should be yyyy-mm-dd,yyyy-mm-dd"
            return

        # Check if they entered any dates or periods
        if start > end:
            print "The period must no end before it starts"
            return

        # ------------------------------------------------------------------------
        # Helper functions
        # ------------------------------------------------------------------------

        def radar_factory(num_vars, frame='circle'):
            # calculate evenly-spaced axis angles
            theta = 2*np.pi * np.linspace(0, 1-1./num_vars, num_vars)
            # rotate theta such that the first axis is at the top
            theta += np.pi/2

            def draw_poly_patch(self):
                verts = unit_poly_verts(theta)
                return plt.Polygon(verts, closed=True, edgecolor='k')

            def draw_circle_patch(self):
                # unit circle centered on (0.5, 0.5)
                return plt.Circle((0.5, 0.5), 0.5)

            patch_dict = {'polygon': draw_poly_patch, 'circle': draw_circle_patch}
            if frame not in patch_dict:
                raise ValueError('unknown value for `frame`: %s' % frame)

            class RadarAxes(PolarAxes):

                name = 'radar'
                # use 1 line segment to connect specified points
                RESOLUTION = 1
                # define draw_frame method
                draw_patch = patch_dict[frame]

                def fill(self, *args, **kwargs):
                    """Override fill so that line is closed by default"""
                    closed = kwargs.pop('closed', True)
                    return super(RadarAxes, self).fill(closed=closed, *args, **kwargs)

                def plot(self, *args, **kwargs):
                    """Override plot so that line is closed by default"""
                    lines = super(RadarAxes, self).plot(*args, **kwargs)
                    for line in lines:
                        self._close_line(line)

                def _close_line(self, line):
                    x, y = line.get_data()
                    # FIXME: markers at x[0], y[0] get doubled-up
                    if x[0] != x[-1]:
                        x = np.concatenate((x, [x[0]]))
                        y = np.concatenate((y, [y[0]]))
                        line.set_data(x, y)

                def set_varlabels(self, labels):
                    self.set_thetagrids(theta * 180/np.pi, labels)

                def _gen_axes_patch(self):
                    return self.draw_patch()

                def _gen_axes_spines(self):
                    if frame == 'circle':
                        return PolarAxes._gen_axes_spines(self)
                    # The following is a hack to get the spines (i.e. the axes frame)
                    # to draw correctly for a polygon frame.

                    # spine_type must be 'left', 'right', 'top', 'bottom', or `circle`.
                    spine_type = 'circle'
                    verts = unit_poly_verts(theta)
                    # close off polygon by repeating first vertex
                    verts.append(verts[0])
                    path = Path(verts)

                    spine = Spine(self, spine_type, path)
                    spine.set_transform(self.transAxes)
                    return {'polar': spine}

            register_projection(RadarAxes)
            return theta


        def unit_poly_verts(theta):
            x0, y0, r = [0.5] * 3
            verts = [(r*np.cos(t) + x0, r*np.sin(t) + y0) for t in theta]
            return verts




        def get_data(profiles, start, end, open_or_not):

            # Get channels
            channel_gas  = Channel.objects.all().get(name='Gas')  
            channel_elec = Channel.objects.all().get(name='Electricity')  
            channel_open = Channel.objects.all().get(name__icontains='Opening') 

            # Init vars
            data = { 'column names': range(0,24), }

            # Load sensors
            if len(profiles) > 0:
                profiles = profiles
            else:
                profiles = Sensor_profile.objects.all()

            # For each sensor process the readings
            for profile in profiles:
                key       = str(profile.sensor.mac)+' '+str(profile.sensor.name)
                data[key] = []
                
                # Process channels
                for channel in [channel_gas, channel_elec, channel_open]:

                    # Load readings
                    readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(start, end), channel=channel)

                    # Process Readings
                    l = [0] * 24
                    for r in readings:
                        k     = int(r.timestamp.strftime('%H'))
                        # open_or_not
                        if channel == channel_open and open_or_not:
                            if r.value > 0:
                                l[k] = 1
                        else:
                            l[k] += r.value


                    # Normalise?
                    if options['normalize']:
                        if sum(l) > 0:
                            l = [float(i)/max(l) for i in l]
                    
                    data[key].append(l)
            

            return data




        # ------------------------------------------------------------------------
        # Start of run code
        # ------------------------------------------------------------------------

        profiles = []
        if options['sensor_list']:
            for sensor_name in options['sensor_list']:
                # Is the sensor name a number i.e. the MAC address
                try:
                    int(sensor_name)
                    sensor_name_is_number = True
                except:
                    sensor_name_is_number = False
                # Get the sensors of the site type
                try:
                    if sensor_name_is_number:
                        profile = Sensor_profile.objects.get(sensor__mac=sensor_name)
                        profiles.append(profile)
                    else:
                        profile = Sensor_profile.objects.get(longname__icontains=sensor_name)
                        profiles.append(profile)
                except Sensor_profile.DoesNotExist:
                    print "Failed to find sensor:",sensor_name,sensor_name_is_number
                    return
                except Sensor_profile.MultipleObjectsReturned:
                    print "Sensor name entered ("+sensor_name+") did not return a unique sensor."
                    return


        data = get_data(profiles,start,end,options['open_or_not'])

        N = len(data['column names'])
        spoke_labels = data.pop('column names')
        theta = radar_factory(N, frame='polygon')

        number_cols = 6
        number_rows = int( math.ceil( float( len(data) ) / float(number_cols) ) )

        print number_cols, number_rows

        fig = plt.figure(figsize=(4 * number_cols, 4 * number_rows))
        fig.subplots_adjust(wspace=0.25, hspace=0.20, top=0.85, bottom=0.05)

       
        colors = ['b', 'r', 'g', 'm', 'y']
        # Plot the four cases from the example data on separate axes
        for n, title in enumerate(data.keys()):
            ax = fig.add_subplot(number_rows, number_cols, n+1, projection='radar')
            plt.rgrids([0.2, 0.4, 0.6, 0.8])
            ax.set_title(title, weight='bold', size='medium', position=(0.5, 1.1),
                         horizontalalignment='center', verticalalignment='center')
            for d, color in zip(data[title], colors):
                ax.plot(theta, d, color=color)
                ax.fill(theta, d, facecolor=color, alpha=0.25)
            ax.set_varlabels(spoke_labels)

            # add legend relative to top-left plot
            if n == 0:
                labels = ('Gas', 'Electricity', 'Opening Hrs')
                ax.legend(labels, loc='upper center', bbox_to_anchor=(0.1, 1.8))

    
        plt.figtext(0.5, 0.965, ' Gas, Electicity and Opening Hours -- '+start.strftime('%Y-%m-%d')+' to '+end.strftime('%Y-%m-%d'),
                    ha='center', color='black', weight='bold', size='large')

        

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
    

                
                
