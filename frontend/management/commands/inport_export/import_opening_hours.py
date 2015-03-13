#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
import datetime, os
from frontend.models import *
import matplotlib.pyplot as plt
from optparse import make_option
import numpy as np
from datetime import datetime
import time
import csv

class Command(BaseCommand):
    
    help = 'Populates the db from CSV file(s)'
    option_list = BaseCommand.option_list + (
    make_option('--file',
                    action='append',
                    dest='files',
                    default=None,
                    help='File to import'),
                )

    def handle(self, *args, **options):


        bankholidays = {}
        bankholidays[2014] = [
            datetime.strptime('25-8-2014 00:00', '%d-%m-%Y %H:%M'),
            datetime.strptime('26-5-2014 00:00', '%d-%m-%Y %H:%M'),
            datetime.strptime('5-5-2014 00:00', '%d-%m-%Y %H:%M'),
            datetime.strptime('21-4-2014 00:00', '%d-%m-%Y %H:%M'),
            datetime.strptime('18-4-2014 00:00', '%d-%m-%Y %H:%M'),
            datetime.strptime('1-1-2014 00:00', '%d-%m-%Y %H:%M'),
            datetime.strptime('26-12-2013 00:00', '%d-%m-%Y %H:%M'),
            datetime.strptime('25-12-2013 00:00', '%d-%m-%Y %H:%M'),
        ]
        
        data = {}

        if options['files'] == None:
            print "Please specify at least one file to import using --file"
            return

        # Import the CSV
        for filename in options['files']:
            print "Importing "+filename
            rows = csv.DictReader(open(filename, 'rU'))

            # Loop through each day (row)
            for row in rows:
                day_of_week = row['']

                # Loop through each site (col)
                for k in row:
                    
                    if k == '':
                        print "K blank:", k
                        continue

                    site_data  = k.split(' - ')
                    if len(site_data) != 2:
                        print 'Failed to split:', k
                        continue

                    site_name  = site_data[1]
                    site_num   = site_data[0]
                    
                    
                    try:
                        profile     = Sensor_profile.objects.get(sensor__mac=site_num)
                    except:
                        print "Failed to locate site:", site_name, site_num
                    
                    if row[k] == '-':
                        # print site_name, site_num, day_of_week, 'closed'
                        continue
                    else:
                        hours      = row[k].split(' to ')
                        if len(hours) != 2:
                            hours      = row[k].split('-')
                    
                        if len(hours) != 2:
                            print "Not 2 hours - "+row[k]
                        
                   
                    try:
                        ts_open  = datetime.strptime('1-1-2014 '+hours[0].strip(), '%d-%m-%Y %I.%M%p')
                        ts_close = datetime.strptime('1-1-2014 '+hours[1].strip(), '%d-%m-%Y %I.%M%p')
                    except:
                        print site_name, site_num,
                        print hours[0]
                        print hours[1]
                        return

                    if site_name not in data:
                        data[site_name] = { 'profile':profile }

                    data[site_name][day_of_week] = { 'open': ts_open, 'close': ts_close }
                    # print site_name, site_num, day_of_week, ts_open, '-->', ts_close

        # Once Data is build process it
        year    = 2014
        seasons = get_season_dates(year)
        start_date = seasons['winter']['start']
        end_date   = seasons['autumn']['end']
        day_count = (end_date - start_date).days + 1

        counter = 0

        for site_name in data:
            counter += 1
            print data[site_name]['profile'].sensor.mac
            print counter, 'of', len(data)

            channel, created = Channel.objects.get_or_create(name='Opening Hours', unit='30mins', reading_frequency=1800)

            # Loop through days of the year
            for single_date in (start_date + timedelta(n) for n in range(day_count)):
                
                dayname = single_date.strftime('%A')
                # print site_name, single_date, dayname
                
                # Are there opening times for this day?
                if dayname in data[site_name] and single_date not in bankholidays[year]:
                    ts_open  = data[site_name][dayname]['open']
                    ts_close = data[site_name][dayname]['close']

                    # loop through hours in the day
                    now = single_date
                    end = now + timedelta(days=1)

                    ts_today_open  = datetime(single_date.year, single_date.month, single_date.day, ts_open.hour,  ts_open.minute)
                    ts_today_close = datetime(single_date.year, single_date.month, single_date.day, ts_close.hour, ts_close.minute)

                    # Open or closed
                    while now < end:
                        if now > ts_today_open and now <= ts_today_close:
                            r = 1
                        else:
                            r = 0
                        reading, created = SensorReading.objects.get_or_create(timestamp=now, sensor=data[site_name]['profile'].sensor, channel=channel)
                        reading.value = r
                        reading.save()
                        now += timedelta(minutes=30)

                # No then fill the day with zeros
                else:
                    # loop through hours in the day
                    now = single_date
                    end = now + timedelta(days=1)
                    # Open or closed
                    while now < end:
                        reading, created = SensorReading.objects.get_or_create(timestamp=now, sensor=data[site_name]['profile'].sensor, channel=channel)
                        reading.value = 0
                        reading.save()
                        now += timedelta(minutes=30)


            
        
  

