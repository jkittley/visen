#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from sd_store.models import Sensor, SensorReading

from datetime import datetime
from optparse import make_option
import numpy as np
from os import makedirs
import csv

day_check = lambda x: x.hour >= 8 and x.hour <= 18
weekday_check = lambda x: x.weekday() not in (5,6)

class Command(BaseCommand):
    help = 'Generate derived CSV from multiple sensors'
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
        make_option('--channel',
                    dest='channel',
                    default=None,
                    help='Channel to use'),
        )


    def make_row(self, date, values, wday_day, wday_night):
        return [date, np.min(values), np.max(values), np.mean(values), wday_day, wday_night]

    def plot_grouped_data(self, username, sensorname, data):
        grouped = {}
        dates = []
        for x in data:
            date = x[0].date()
            try:
                grouped[date].append(x)
            except KeyError:
                grouped[date] = [x,]
            if not date in dates:
                dates.append(date)
        csvfile = open('/Users/moj/Data/bourne/derived/'+sensorname+'.csv', 'wb')
        writer = csv.writer(csvfile)
        for date in dates:
            l = grouped[date]
            if weekday_check(date):
                day_values = [x[1] for x in l if day_check(x[0])]
                night_values = [x[1] for x in l if not day_check(x[0])]
                if len(day_values) > 0:
                    writer.writerow(self.make_row(date, day_values, True, False))
                if len(night_values) > 0:
                    writer.writerow(self.make_row(date, night_values, False, True))
                all_values = [x[1] for x in l]
                if len(all_values) > 0:
                    writer.writerow(self.make_row(date, all_values, True, True))
            else:
                values = [x[1] for x in l]
                if len(values) > 0:
                    writer.writerow(self.make_row(date, values, False, False))

    def handle(self, *args, **options):
        usernames = options['user']
        includes = options['include']
        excludes = options['exclude']
        startdate = options['start']
        enddate = options['end']
        channel = options['channel']

        if not startdate:
            print "Start date is required"
            return
        if not enddate:
            print "End date is required"
            return
        if not channel:
            print "Channel is required"
            return

        startdate = datetime.strptime(options['start'], "%Y-%m-%d")
        enddate = datetime.strptime(options['end'], "%Y-%m-%d")

        for username in usernames:
            user = User.objects.get(username=username)
            sensors = Sensor.objects.filter(user=user)
            for sensor in sensors:

                if excludes != None and sensor.name in excludes:
                    continue
                if includes != None and not sensor.name in includes:
                    continue

                c = sensor.channels.get(name=channel)
                try:
                    makedirs('plots/'+username+'/'+sensor.name)
                except:
                    # TODO: Skip error if already exists
                    pass
    
                readings = SensorReading.objects.filter(sensor=sensor, channel=c).values_list('timestamp', 'value')
                self.plot_grouped_data(username, sensor.name, readings)