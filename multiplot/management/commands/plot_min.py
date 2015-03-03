#encoding:UTF-8
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User

from sd_store.models import Channel, Sensor, SensorReading
from sd_store.sdutils import get_meter, NoPrimaryMeterException
from sd_store.statutils import dump_header, dump_stats, daily, weekly, monthly, group_data, smooth, parse_readings
import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from optparse import make_option
import numpy as np
import csv
import time

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

        #ylabel = channel.name+' ('+channel.unit+')'

        datemin = datetime.max
        datemax = datetime.min
        styles = ['r', 'b', 'm', 'c', 'g', 'y', 'r--', 'g--', 'b--', 'c--', 'm--']

        i = 0

        allts = []
        series = []
        sensornames = []

        stats_out = []
        stats_out.append(dump_header())
        for username in usernames:
            user = User.objects.get(username=username)
            sensors = Sensor.objects.filter(user=user)
            totalmap = {}
            for sensor in sensors:
                timestamps = []
                values = []
                print sensor.name
                if excludes != None and sensor.name in excludes:
                    continue
                if includes != None and not sensor.name in includes:
                    continue
                CHANNEL = 'power'
                try:
                    channel = sensor.channels.get(name=CHANNEL)
                except Channel.DoesNotExist:
                    print "No channel"
                    continue
                readings = SensorReading.objects.filter(
                    sensor=sensor,
                    timestamp__gt=startdate,
                    timestamp__lt=enddate,
                    channel=channel)
                data = parse_readings(readings)
                if len(data) == 0:
                    continue
                timestamps, values = zip(*data)
                smoothed_values = smooth(sensor, channel, values)

                # Recreate the data arrays using smoothed readings
                data = zip(timestamps, smoothed_values)
                grouped = group_data(data, index=weekly)
                timestamps = grouped.keys()
                timestamps.sort()
                values = []
                ts_ints = []
                result = []
                sums = []
                mins = []
                for ts in timestamps:
                    mins.append(min([x[1] for x in grouped[ts]]))
                    sums.append(sum([x[1] for x in grouped[ts]]))
                    ts_ints.append(time.mktime(ts.timetuple()))

                ratios = []
                # Work out ratio
                for i, ts in enumerate(timestamps):
                    baseline = len(grouped[ts]) * mins[i]
                    ratios.append(baseline/sums[i])
                ratio = np.mean(ratios)

                a, b = np.polyfit(ts_ints,mins,1)
                stats = dump_stats(sensor, mins)
                stats.append(a*10E6)
                stats.append(ratio)
                stats_out.append(stats)

                fig, ax = plt.subplots()
                ax.xaxis.set_minor_locator(mdates.AutoDateLocator())
                ax.plot(timestamps, mins, styles[i % len(styles)], label=sensor.name)
                ax.plot([x[0] for x in data], [x[1] for x in data])
                ax.set_title(sensor.name)
                ax.plot(timestamps, a*np.array(ts_ints)+b, '--k')
                #plt.savefig('/Users/moj/plots/analysis/base_weekly_'+sensor.name+'.pdf')
                i = i + 1

        writer = csv.writer(self.stdout, dialect='excel-tab', lineterminator='\n')

        for result in stats_out:
            writer.writerow(result)
        if i == 0:
            print "No sensors plotted."
            return

        plt.show()
