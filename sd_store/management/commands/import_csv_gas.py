#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.transaction import commit_on_success
from django.contrib.auth.models import User
from optparse import make_option
from sd_store.models import Channel, Sensor, SensorReading
from datetime import datetime, timedelta
from django.contrib.auth.models import User
import csv
from decimal import *

class Command(BaseCommand):
    help = 'Populates the db from CSV file(s)'
    option_list = BaseCommand.option_list + (
        make_option('--user',
                    dest='user',
                    default=None,
                    help='Select a specific user'),
        make_option('--file',
                    action='append',
                    dest='files',
                    default=None,
                    help='Files to import'),
        )
    
    def handle(self, *args, **options):
        if options['files'] == None:
            print "Please specify at least one file to import using --file"
            return

        if options['user'] == None:
            print "Please specify at least one user to import as using --user"
            return

        user = User.objects.get(username=options['user'])
        # Energy (kWh) every 30 minutes
        rate = 1800
        time_delta = timedelta(seconds=rate)
        CHANNEL = 'energy'
        channel, created = Channel.objects.get_or_create(name=CHANNEL, unit='kWh', reading_frequency=rate)
        
        self.stdout.write("populating sd_store..\n")
        for filename in options['files']:
            print "Importing "+filename
            rows = csv.reader(open(filename, 'rU'))
            sensor, created = Sensor.objects.get_or_create(mac='TotalGas', name='TotalGas', user=user)
            sensor.channels.add(channel)
            for row in rows:
                if row[0] != ' ':
                    # Reset start ts
                    ts = datetime.strptime(row[0], "%d/%m/%Y")
                v = Decimal(row[1]) + Decimal(row[2])
                print v
                ts = ts + time_delta
                print ts
                reading, created = SensorReading.objects.get_or_create(timestamp=ts, sensor=sensor, channel=channel)
                reading.value = v
                reading.save()