#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from sd_store.models import Channel, Sensor, SensorReading
from datetime import datetime

from optparse import make_option
class Command(BaseCommand):
    help = 'Generates a sensor derived by summing several sensors'
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
        make_option('--name',
                    dest='name',
                    default='total',
                    help='Name of generated sensor'),
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
                    help='Name of channel to use (e.g. energy)'),
        make_option('--rate',
                    dest='rate',
                    default=0,
                    help='Reading frequency'),
        )
    def handle(self, *args, **options):
        if options['user'] == None:
            print "Please specify at least one user to import as using --user"
            return

        usernames = options['user']

        includes = options['include']
        excludes = options['exclude']
        startdate = options['start']
        enddate = options['end']
        name = options['name']
        if startdate:
            startdate = datetime.strptime(options['start'], "%Y-%m-%d")

        if enddate:
            enddate = datetime.strptime(options['end'], "%Y-%m-%d")
        channel = Channel.objects.get(name=options['channel'], reading_frequency=options['rate'])

        datemin = datetime.max
        datemax = datetime.min

        i = 0
        for username in usernames:
            user = User.objects.get(username=username)
            sensors = Sensor.objects.filter(user=user)
            totalmap = {}
            for sensor in sensors:
                if excludes != None and sensor.mac in excludes:
                    continue
                if includes != None and not sensor.mac in includes:
                    continue
                if sensor.mac == name:
                    continue

                print "Read all from ", sensor
                readings = SensorReading.objects.filter(sensor=sensor, channel=channel)
                if startdate:
                    readings = readings.filter(timestamp__gte=startdate)
                if enddate:
                    readings = readings.filter(timestamp__lte=enddate)

                for reading in readings:

                    # Update total - using a map as sensors may not all have readings for some times
                    if not reading.timestamp in totalmap:
                        totalmap[reading.timestamp] = reading.value
                    else:
                        totalmap[reading.timestamp] = totalmap[reading.timestamp] + reading.value

                i = i + 1

        if i == 0:
            print "No sensors found."
            return

        total_sensor, created = Sensor.objects.get_or_create(mac=name, name=name, user=user, sensor_type='Derived Total')
        totaltimes = totalmap.keys()
        totaltimes.sort()
        for ts in totaltimes:
            v = totalmap[ts]
            reading, created = SensorReading.objects.get_or_create(timestamp=ts, sensor=total_sensor, channel=channel, value=v)
            reading.save()
