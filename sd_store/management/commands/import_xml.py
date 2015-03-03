#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.transaction import commit_on_success
from django.contrib.auth.models import User
from bs4 import BeautifulSoup, SoupStrainer
from optparse import make_option
from sd_store.models import Channel, Sensor, SensorReading
import datetime
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Populates the db from XML file(s)'
    option_list = BaseCommand.option_list + (
        make_option('--user',
                    dest='user',
                    default=None,
                    help='Select a specific user'),
        make_option('--quick',
                    action='store_true',
                    dest='quick',
                    default=False,
                    help='Do not update the devices information, just get the data'),
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
        tags = SoupStrainer('timestamps_collection')

        user = User.objects.get_or_create(username=options['user'])
        # Appears to be power (kW) every 15 minutes (900s)
        rate = 900
        power, created = Channel.objects.get_or_create(name='power', unit='kW', reading_frequency=rate)
        
        self.stdout.write("populating sd_store..\n")
        for filename in options['files']:
            print "Importing "+filename
            soup = BeautifulSoup(open(filename), 'lxml')
            for devicename in soup.find_all('devicenames'):
                name = devicename['label'][0:32]
                print "Device: "+name
                sensor, created = Sensor.objects.get_or_create(mac=name, name=name, user=user)
                for timestamp in devicename.series0.timestamps_collection:
                    if timestamp.has_attr('datavalue0'):
                        ts = datetime.datetime.strptime(timestamp['label'], "%Y-%m-%dT%H:%M:%S")
                        v = timestamp['datavalue0']
                        reading, created = SensorReading.objects.get_or_create(timestamp=ts, sensor=sensor, channel=power)
                        reading.value = v
                        reading.save()
                