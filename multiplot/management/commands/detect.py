#encoding:UTF-8
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User

from sd_store.models import Sensor, SensorReading
from sd_store.sdutils import filter_according_to_interval_gen

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from optparse import make_option
import numpy as np
from os import makedirs

day_check = lambda x: x.hour >= 8 and x.hour <= 18
weekday_check = lambda x: x.weekday() not in (5,6)

THRESHOLD = 70.0

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

    def detect_sig_readings(self, readings):
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
            if weekday_check(date):
                day_values = [x[1] for x in l if day_check(x[0])]
                night_values = [x[1] for x in l if not day_check(x[0])]

                day.append(sum(day_values))
                night.append(sum(night_values))
                working_days.append(sum([x[1] for x in l]))
            else:
                weekend_days.append(sum([x[1] for x in l]))

        labels = ['weekend_days', 'working_days', 'day', 'night']
        total_data = [weekend_days, working_days, day, night]

        v_uw = {}
        v_uq = {}
        v_lq = {}
        v_lw = {}
        v_med = {}

        for i, d in enumerate(total_data):
            k = labels[i]
            v_lq[k] = np.percentile(d, 25)
            v_uq[k] = np.percentile(d, 75)
            # Interquartile range (whiskers are at uq + (1.5*iq), lq - (1.5*iq))
            iq = v_uq[k] - v_lq[k]

            # Calculate whiskers
            # Upper whisker
            hi_val = v_uq[k] + 1.5 * iq
            v_uw[k] = np.compress(d <= hi_val, d)
            if len(v_uw[k]) == 0 or np.max(v_uw[k]) < v_uq[k]:
                v_uw[k] = v_uq[k]
            else:
                v_uw[k] = max(v_uw[k])

            # Lower whisker
            lo_val = v_lq[k] - 1.5 * iq
            v_lw[k] = np.compress(d >= lo_val, d)
            if len(v_lw[k]) == 0 or np.min(v_lw[k]) > v_uq[k]:
                v_lw[k] = v_lq[k]
            else:
                v_lw[k] = min(v_lw[k])
            v_med[k] = np.median(d)

        print v_lw
        print v_med
        print v_uw

        detect_lw = lambda s, t: v_lw[t] <= s <=  (v_lw[t] + THRESHOLD)
        detect_uw = lambda s, t: v_uw[t] - THRESHOLD <= s <=  v_uw[t]

        sig_days = []
        sig_nights = []
        sig_working = []
        sig_weekend = []

        for date, l in grouped.items():
            if weekday_check(date):
                day_values = [x[1] for x in l if day_check(x[0])]
                night_values = [x[1] for x in l if not day_check(x[0])]
                day_sum = sum(day_values)
                night_sum = sum(night_values)
                working_days_sum = sum([x[1] for x in l])

                if detect_uw(day_sum, 'day'): sig_days.append((date, day_sum))
                if detect_uw(night_sum, 'night'): sig_nights.append((date, night_sum))
                if detect_uw(working_days_sum, 'working_days'): sig_working.append((date, working_days_sum))

            else:
                weekend_days_sum = sum([x[1] for x in l])
                if detect_uw(weekend_days_sum, 'weekend_days'): sig_weekend.append((date, weekend_days_sum))

        return {'day':sig_days, 'night':sig_nights, 'working_days':sig_working, 'weekend_days':sig_weekend}

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

        for username in usernames:
            user = User.objects.get(username=username)
            sensors = Sensor.objects.filter(user=user)
            for sensor in sensors:

                if excludes != None and sensor.name in excludes:
                    continue
                if includes != None and not sensor.name in includes:
                    continue

                CHANNEL = 'power'
                channel = sensor.channels.get(name=CHANNEL)
                print sensor, channel, startdate, enddate
                
                readings = SensorReading.objects.filter(
                    sensor=sensor, 
                    timestamp__gt=startdate, 
                    timestamp__lt=enddate,
                    channel=channel)
                # print readings
                # data÷ = [(x.timestamp, x.value) for x in readings]

                # readings =  filter_according_to_interval_gen(sensor, channel, startdate, enddate, 60*60, CHANNEL)
                sig_readings = self.detect_sig_readings(readings)
                print sig_readings
                # try:
                #     makedirs('plots/'+username+'/'+sensor.name)
                # except:
                #     pass
                # for key in ['day', 'night', 'working_days', 'weekend_days']:
                    
                #     print "Key",key
                #     dataset = sig_readings[key]
                #     for ts, s in dataset:
                #         ts2 = ts + timedelta(days=1)
                #         date_readings = SensorReading.objects.filter(sensor=sensor, channel=channel, timestamp__gt=ts, timestamp__lt=ts2)
                #         # date_readings =  filter_according_to_interval_gen(sensor, channel, ts, ts2, 60, 'power')
                #         data = [(x.timestamp, x.value) for x in date_readings]
                #         values = [x[1] for x in data]
                #         timestamps = [x[0] for x in data]
                        
                #         fig, ax = plt.subplots()
                #         plt.title(ts.strftime('%a %b %d, %Y')+' ('+key+')')
                #         ax.xaxis.set_minor_locator(mdates.AutoDateLocator())
                #         ax.plot(timestamps, values)
                #         plt.savefig('plots/'+username+'/'+sensor.name+'/'+ts.strftime('%Y-%m-%d')+'_'+key+'.pdf')

        plt.show()