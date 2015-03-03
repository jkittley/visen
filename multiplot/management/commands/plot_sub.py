#encoding:UTF-8
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User

from sd_store.models import Channel, Sensor, SensorReading
from sd_store.sdutils import get_meter, NoPrimaryMeterException

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from optparse import make_option
import csv
import numpy as np

class Command(BaseCommand):
    help = 'Plots data from multiple sensors'
    option_list = BaseCommand.option_list + (
        make_option('--user',
                    dest='user',
                    default=None,
                    help='User to plot'),
        make_option('--s1',
                    dest='s1',
                    default=None,
                    help='Sensor 1'),
        make_option('--s2',
                    dest='s2',
                    default=None,
                    help='Sensors 2'),
        make_option('--start',
                    dest='start',
                    default=None,
                    help='Start date YYYY-MM-DD'),
        make_option('--end',
                    dest='end',
                    default=None,
                    help='End date YYYY-MM-DD'),
        make_option('--title',
                    dest='title',
                    default=None,
                    help='title'),
        make_option('--out',
                    dest='out',
                    default=None,
                    help='output prefix'),
        )

    def get_sensor_data(self, sensor, startdate, enddate):
        readings = SensorReading.objects.filter(
            sensor=sensor,
            timestamp__gt=startdate,
            timestamp__lt=enddate)
        data = [(x.timestamp, x.value) for x in readings]
        return data

    def handle(self, *args, **options):
        username = options['user']
        s1 = options['s1']
        s2 = options['s2']
        startdate = options['start']
        enddate = options['end']
        out = options['out']
        title = options['title']
        if startdate:
            startdate = datetime.strptime(options['start'], "%Y-%m-%d")

        if enddate:
            enddate = datetime.strptime(options['end'], "%Y-%m-%d")

        fig, ax = plt.subplots()
        ax.xaxis.set_minor_locator(mdates.AutoDateLocator())

        #ylabel = channel.name+' ('+channel.unit+')'

        datemin = datetime.max
        datemax = datetime.min
        styles = ['r', 'b', 'm', 'c', 'g', 'y', 'r--', 'g--', 'b--', 'c--', 'm--']

        i = 0

        allts = []
        series = []
        sensornames = []

        user = User.objects.get(username=username)
        sensor_1 = Sensor.objects.get(name=s1, user=user)
        sensor_2 = Sensor.objects.get(name=s2, user=user)
        totalmap = {}
        timestamps = []
        values = []

        data_1 = dict((x,y) for x,y in self.get_sensor_data(sensor_1, startdate, enddate))

        data_2 = dict((x, y) for x,y in self.get_sensor_data(sensor_2, startdate, enddate))

        # Probably a much tidier way to do this!
        subbed = {}
        for k,v in data_1.iteritems():
            if k in data_2:
                subbed[k] = v-data_2[k]

        data =  sorted(subbed.iteritems())

        window_size = (3 * 60 * 60) / (15*60)
        window = (np.zeros(int(window_size)) + 1.0) / window_size
        tmp = [x[1] for x in data]
        tmp_mav = np.convolve(tmp, window, 'same')
        data = zip([x[0] for x in data], tmp_mav)

        values = [x[1] for x in data]
        timestamps = [x[0] for x in data]

        for ts in timestamps:
            trimmed = datetime.strftime(ts, '%Y-%m-%d %H:%M')
            if trimmed not in allts:
                allts.append(trimmed)
        ax.plot(timestamps, values, styles[i % len(styles)], label=s1+" - "+s2)
        if len(timestamps) > 0:
            if timestamps[0] < datemin:
                datemin = timestamps[0]
            if timestamps[-1] > datemax:
                datemax = timestamps[-1]


        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], ncol=3, prop={'size':8}, bbox_to_anchor=(1.0, 1.08))
        ax.set_ylabel(u"Power (kW)")
        ax.set_title(title)
        ax.set_xlim(datemin, datemax)
        fig.autofmt_xdate()
        plt.show()
