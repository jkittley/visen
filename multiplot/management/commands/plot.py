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
        make_option('--ymin',
                    dest='ymin',
                    default=None,
                    help='y min'),
        make_option('--ymax',
                    dest='ymax',
                    default=None,
                    help='y max'),
        make_option('--title',
                    dest='title',
                    default=None,
                    help='title'),
        make_option('--out',
                    dest='out',
                    default=None,
                    help='output prefix'),
        )

    def handle(self, *args, **options):
        usernames = options['user']
        includes = options['include']
        excludes = options['exclude']
        startdate = options['start']
        enddate = options['end']
        ymin = options['ymin']
        ymax = options['ymax']
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

        for username in usernames:
            user = User.objects.get(username=username)
            sensors = Sensor.objects.filter(user=user)
            totalmap = {}
            for sensor in sensors:
                timestamps = []
                values = []

                if excludes != None and sensor.name in excludes:
                    continue
                if includes != None and not sensor.name in includes:
                    continue
                readings = SensorReading.objects.filter(
                    sensor=sensor,
                    timestamp__gt=startdate,
                    timestamp__lt=enddate)
                data = [(x.timestamp, x.value) for x in readings]

                # window_size = (3 * 60 * 60) / (15*60)
                # window = (np.zeros(int(window_size)) + 1.0) / window_size
                # tmp = [x[1] for x in data]
                # tmp_mav = np.convolve(tmp, window, 'same')
                # data = zip([x[0] for x in data], tmp_mav)

                tdata = [(datetime.strftime(x.timestamp, '%Y-%m-%d %H:%M'), x.value) for x in readings]
                series.append(dict(tdata))
                sensornames.append(sensor.name)
                values = [x[1] for x in data]
                if sensor.name == 'TotalGas':
                    values = [v/10.0 for v in values]
                timestamps = [x[0] for x in data]
                for ts in timestamps:
                    trimmed = datetime.strftime(ts, '%Y-%m-%d %H:%M')
                    if trimmed not in allts:
                        allts.append(trimmed)
                ax.plot(timestamps, values, styles[i % len(styles)], label=sensor.name)
                if len(timestamps) > 0:
                    if timestamps[0] < datemin:
                        datemin = timestamps[0]
                    if timestamps[-1] > datemax:
                        datemax = timestamps[-1]

                i = i + 1

        if i == 0:
            print "No sensors plotted."
            return

        # print series
        # allts.sort()
        # with open('/Users/moj/plots/Workshop/'+out+'.csv', 'wb') as csvfile:
        #     writer = csv.writer(csvfile)
        #     head = ["Time",]
        #     for sensorname in sensornames: head.append(sensorname)
        #     writer.writerow(head)
        #     for ts in allts:
        #         row = [ts,]
        #         for s in series:
        #             if ts in s:
        #                 row.append(s[ts])
        #             else:
        #                 row.append('')
        #         writer.writerow(row)

        # Plot total line
        # totaltimes = totalmap.keys()
        # totaltimes.sort()
        # totalvals = list((totalmap[k]) for k in totaltimes)
        # ax.plot(totaltimes, totalvals, 'k', label='total')

        handles, labels = ax.get_legend_handles_labels()
        #plt.ylabel(ylabel)
        ax.legend(handles[::-1], labels[::-1], ncol=3, prop={'size':8}, bbox_to_anchor=(1.0, 1.08))
        ax.set_ylabel(u"Power (kW)")
        ax.set_title(title)
        ax.set_xlim(datemin, datemax)
        if ymin and ymax:
            plt.ylim([int(ymin),int(ymax)])
        fig.autofmt_xdate()
        # plt.savefig('/Users/moj/plots/Workshop/'+out+'.svg')
        # plt.savefig('/Users/moj/plots/Workshop/'+out+'.pdf')
        # plt.savefig('/Users/moj/plots/Workshop/'+out+'.png')
        plt.show()
