#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.transaction import commit_on_success
from django.contrib.auth.models import User
from optparse import make_option
from sd_store.models import Channel, Sensor, SensorReading
import datetime
from django.contrib.auth.models import User
import urllib2
import simplejson as json

class Command(BaseCommand):
    help = 'Populates the db from CSV file(s)'
    option_list = BaseCommand.option_list + (
        make_option('--user',
                    dest='user',
                    default=None,
                    help='Select a specific user'),
        )

    def import_sensors(self, user):
        response = urllib2.urlopen('http://energyforchange.ac.uk/energy/bear.json')
        js = json.loads(response.read())
        response.close()
        for key in js['Meters']:
            name = js['Meters'][key]['tag']
            sensor, created = Sensor.objects.get_or_create(mac=key, name=name, user=user)
            if created:
                print "Created sensor", sensor.name
    
    def import_readings(self, user, sensor):
        months = ['08', '09', '10']
        print "Import for", sensor.name
        for month in months:
            url = 'http://energyforchange.ac.uk/energy/5min/S-m%s/S-m%s-2013-%s.json' % (sensor.mac,sensor.mac,month)
            print "Load from "+url
            response = urllib2.urlopen(url)
            js = json.loads(response.read())
            response.close()

            # Fetch/create channel
            name_map = {
                'kW':'power',
                'kWh':'energy',
            }
            unit = js['reading units']
            step = js['data']['step']
            rate = step/1000

            channel, created = Channel.objects.get_or_create(unit=js['reading units'], reading_frequency=rate, name=name_map[unit])
            current_ts = js['data']['start']/1000
            for reading in js['data']['readings']:
                ts = datetime.datetime.fromtimestamp(current_ts)
                sensor_reading, created = SensorReading.objects.get_or_create(timestamp=ts, sensor=sensor, channel=channel)
                sensor_reading.value = reading
                sensor_reading.save()
                current_ts = current_ts + rate

    def handle(self, *args, **options):
        if options['user'] == None:
            print "Please specify at least one user to import as using --user"
            return

        user = User.objects.get(username=options['user'])
        self.import_sensors(user)
        sensors = Sensor.objects.filter(user=user)
        for sensor in sensors:
            self.import_readings(user, sensor)
        return
