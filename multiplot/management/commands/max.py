#encoding:UTF-8
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User

from sd_store.models import Sensor, SensorReading
from sd_store.sdutils import filter_according_to_interval_sqlite

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from optparse import make_option
import numpy as np
from os import makedirs
import csv

day_check = lambda x: x.hour >= 8 and x.hour <= 18
weekday_check = lambda x: x.weekday() not in (5,6)

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
        )

    def plot_grouped_data(self, username, sensorname, readings):
        data = [(x.timestamp, x.value) for x in readings]

        grouped = {}
        for x in data:
            try:
                grouped[x[0].date()].append(x)
            except KeyError:
                grouped[x[0].date()] = [x,]


        weekend_days = []
        working_days = []
        night = []
        day = []


        for date, l in grouped.items():
            # print date
            if weekday_check(date):
                day_values = [x[1] for x in l if day_check(x[0])]
                night_values = [x[1] for x in l if not day_check(x[0])]

                day.append(sum(day_values))
                night.append(sum(night_values))
                working_days.append(sum([x[1] for x in l]))
            else:
                weekend_days.append(sum([x[1] for x in l]))

        labels = ['weekend_days', 'working_days', 'day', 'night']
        data = [weekend_days, working_days, day, night]
        # print data
        for i,d in enumerate(data):
            plt.figure()
            plt.title(labels[i])
            plt.hist(d, 100)
            plt.axis((0,1000,0,50))
            #plt.savefig('plots/'+username+'/'+sensorname+'/'+labels[i]+'.pdf')


        plt.figure()
        plt.title('All values: '+sensorname)
        plt.boxplot(data)
        plt.xticks(range(1,len(labels)+1), labels)
        #plt.savefig('plots/'+username+'/'+sensorname+'/all_values.pdf')


    def handle(self, *args, **options):
        usernames = options['user']
        includes = options['include']
        excludes = options['exclude']
        startdate = options['start']
        enddate = options['end']


        if not startdate:
            print "Start date is required"
            return
        if not enddate:
            print "End date is required"
            return

        startdate = datetime.strptime(options['start'], "%Y-%m-%d")
        enddate = datetime.strptime(options['end'], "%Y-%m-%d")


        # CHANNEL = 'power'
        for username in usernames:
            user = User.objects.get(username=username)
            sensors = Sensor.objects.filter(user=user)
            for sensor in sensors:

                if excludes != None and sensor.name in excludes:
                    continue
                if includes != None and not sensor.name in includes:
                    continue

                channel = sensor.channels.get(name='power')#pk=5)#name=CHANNEL)
                try:
                    makedirs('plots/'+username+'/'+sensor.name)
                except:
                    # TODO: Skip error if already exists
                    pass
                readings = SensorReading.objects.filter(
                    sensor=sensor,
                    timestamp__gt=startdate,
                    timestamp__lt=enddate)
                # readings = filter_according_to_interval_sqlite(sensor, channel, startdate, enddate, 60*60, 'generic')
                self.plot_grouped_data(username, sensor.name, readings)

                data = [(x.timestamp, x.value) for x in readings]
                values = [x[1] for x in data]

                plt.figure()
                plt.title(sensor.name)
                plt.hist(values, 100)
                output = 'P8b'
                # plt.savefig('/Users/moj/plots/Workshop/'+output+'.svg')
                # plt.savefig('/Users/moj/plots/Workshop/'+output+'.pdf')
                # plt.savefig('/Users/moj/plots/Workshop/'+output+'.png')
                # with open('/Users/moj/plots/Workshop/'+output+'.csv', 'wb') as csvfile:
                #     writer = csv.writer(csvfile)
                #     head = [sensor.name,]
                #     writer.writerow(head)
                #     for r in values:
                #         writer.writerow([r,])

        plt.show()
