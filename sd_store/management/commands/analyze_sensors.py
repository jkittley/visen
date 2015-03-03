#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from sd_store.models import Sensor, SensorReading, Channel
from sd_store.sdutils import filter_according_to_interval_gen
import sd_store.statutils as statutils

import csv

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from optparse import make_option
from os import makedirs


class Command(BaseCommand):
    help = 'Plots data from multiple sensors'
    option_list = BaseCommand.option_list + (
        make_option('--user',
                    action='append',
                    dest='user',
                    default=None,
                    help='Users to plot'),
        make_option('--include',
                    action='append',
                    dest='include',
                    default=None,
                    help='Sensors to include'),
        make_option('--exclude',
                    action='append',
                    dest='exclude',
                    default=None,
                    help='Sensors to exclude'),
        make_option('--start',
                    dest='start',
                    default=None,
                    help='Start date YYYY-MM-DD'),
        make_option('--end',
                    dest='end',
                    default=None,
                    help='End date YYYY-MM-DD'),
        make_option('--group',
                    dest='group',
                    default='daily',
                    help='How to group the data (daily, weekly, monthly)'),
        make_option('--type',
                    dest='type',
                    default='summed',
                    help='Whether to work out stats on summed values (summed) or per group (group)')
        )

    def process_readings(self, sensors, channel, startdate, enddate, approach=statutils.cumulative, index=statutils.daily):
        result = []
        if approach == statutils.cumulative:
            result.append(statutils.dump_header(ts=False))          

        for sensor in sensors:
            if approach == statutils.non_cumulative:
                result.append(statutils.dump_header(ts=True))
            readings = SensorReading.objects.filter(
                sensor=sensor, 
                timestamp__gt=startdate, 
                timestamp__lt=enddate,
                channel=channel)
            result.extend(approach(sensor, readings, index))
        return result

    def handle(self, *args, **options):
        usernames = options['user']
        includes = options['include']
        excludes = options['exclude']
        startdate = options['start']
        enddate = options['end']

        group = options['group']
        stype = options['type']

        gmap = {
            'daily':statutils.daily,
            'weekly':statutils.weekly,
            'monthly':statutils.monthly
        }

        smap = {
            'summed':statutils.cumulative,
            'group':statutils.non_cumulative
        }

        if group not in gmap:
            group = 'daily'
        if stype not in smap:
            stype = 'summed'

        g_fn = gmap[group]
        s_fn = smap[stype]

        if not startdate:
            print "Start date is required"
            return
        if not enddate:
            print "End date is required"
            return

        startdate = datetime.strptime(options['start'], "%Y-%m-%d")
        enddate = datetime.strptime(options['end'], "%Y-%m-%d")

        valid_sensors = []
        for username in usernames:
            user = User.objects.get(username=username)
            sensors = Sensor.objects.filter(user=user)
            for sensor in sensors:

                if excludes != None and sensor.name in excludes:
                    continue
                if includes != None and not sensor.name in includes:
                    continue
                CHANNEL = 'power'
                try:
                    channel = sensor.channels.get(name=CHANNEL)
                except Channel.DoesNotExist:
                    continue
                valid_sensors.append(sensor)

        results = self.process_readings(valid_sensors, channel, startdate, enddate, 
            approach=s_fn,
            index=g_fn)
        writer = csv.writer(self.stdout, dialect='excel-tab', lineterminator='\n')

        for result in results:
            writer.writerow(result)
        #self.dump_stats(sensor, values)

        # # Weekend plot
        # data = self.group_data(readings, index=daily)
        # weekends = self.split_day_data(data)['weekend_days']
        # timestamps = [x[0] for x in weekends]
        # values = [x[1] for x in weekends]


        # fig, ax = plt.subplots()      
        # ax.xaxis.set_minor_locator(mdates.AutoDateLocator())
        # ax.plot(timestamps, values)

        # v = np.array(values)
        # window_len = 11

        # s=np.r_[2*v[0]-v[window_len-1::-1],v,2*v[-1]-v[-1:-window_len:-1]]
        # print s
        # w = np.hanning(window_len)

        # y = np.convolve(w/w.sum(),s,mode='same')
        # res = y[window_len:-window_len+1]
        # # window = (np.zeros(int(5)) + 1.0)
        # # mav = np.convolve(values, window, 'same')

        # fig, ax = plt.subplots()      
        # ax.xaxis.set_minor_locator(mdates.AutoDateLocator())
        # ax.plot(timestamps, res)

        # plt.show()