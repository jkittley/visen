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
import csv
import mechanize
import cookielib
import time
import StringIO
import urllib2
import simplejson as json
from frontend.models import Sensor_profile
from django.forms import ValidationError

# 
#  EXAMPLE:  python manage.py import_weather --month 11 --year 2014


class Command(BaseCommand):
    help = 'Populates the db from SystemLink'
    option_list = BaseCommand.option_list + (
        make_option('--month',
                    dest='month',
                    default=None,
                    help='Select a specific a month'),
        make_option('--year',
                    dest='year',
                    default=None,
                    help='Select a specific a year'),
        make_option('--apikey',
                    dest='apikey',
                    default='9194b9d0252a187f9af4fe0f37794',
                    # default='63c9d3256b1b3b68744ef8c9930bb',
                    help='Select a specific a year')
       )
    
    
    def handle(self, *args, **options):

        def get_postcode_validator(country_code):
            # Django 1.3 uses 'UK' instead of GB - this changes in 1.4
            if country_code == 'GB':
                country_code = 'UK'
            module_path = 'django.contrib.localflavor.%s' % country_code.lower()
            try:
                module = __import__(module_path, fromlist=['forms'])
            except ImportError:
                # No forms module for this country
                return lambda x: x

            fieldname_variants = ['%sPostcodeField',
                                  '%sPostCodeField',
                                  '%sPostalCodeField',
                                  '%sZipCodeField',]
            for variant in fieldname_variants:
                fieldname = variant % country_code.upper()
                if hasattr(module.forms, fieldname):
                    return getattr(module.forms, fieldname)().clean
            return lambda x: x


        def is_postcode_valid(postcode, country_code):
            try:
                get_postcode_validator(country_code)(postcode)
            except ValidationError:
                return False
            return True

        def fetch_temp_data(postcode):
            sm = int(options['month'])
            sy = int(options['year'])
            em = sm + 1
            ey = sy
            if em > 12:
                em  = 1
                ey += 1
            start_date  = "01-"+str(sm)+"-"+str(sy)
            end_date    = "01-"+str(em)+"-"+str(ey)

            path =  'http://api.worldweatheronline.com/premium/v1/past-weather.ashx?q='
            path += postcode
            path += '&format=json&date='
            path += start_date
            path += '&enddate='
            path += end_date
            path += '&key='
            path += API_KEY

            print "Connecting to: ",path

            attempt     = 1
            maxattempts = 10
            response    = None

            while attempt <= maxattempts:

                print "Attempt "+str(attempt)+" of "+str(maxattempts)

                try:
                    response = urllib2.urlopen(path)
                    break;
                except urllib2.HTTPError, e:
                    if e.code == 429:
                        raise SystemExit, "API Limit reached"
                    else:
                        print "Failed to connect. Will try again in 5 seconds"
                        time.sleep(5)
                        attempt += 1
                except:
                    print "Failed to connect. Will try again in 5 seconds"
                    time.sleep(5)
                    attempt += 1

            if response == None:
                print "Maximum attempts reached"
                return None

            # Read responce json data
            js = json.loads(response.read())
            response.close()

            try:
                return js['data']['weather']
            except:
                print "Failed to access js['data']['weather']"
                return None

        # -------------------------------------------------------

        # Clear the screen
        for i in range(1,30):
            print " "

        API_KEY = options['apikey']

        if options['month'] == None:
            print "Please specify a month"
            return

        if options['year'] == None:
            print "Please specify a year"
            return

        # Get some basics
        user    = User.objects.all()[:1].get()
        channel = Channel.objects.get(name='Temp (Feels like)')

        postcodes = Sensor_profile.objects.order_by().values_list('postcode').distinct() 
        unique_postcodes = []
        for p in postcodes:

            if is_postcode_valid(p[0],"GB"):

                firstbit = str(p[0][:4])
                if not firstbit in unique_postcodes:
                    unique_postcodes.append(firstbit)
            else:
                print "Invalid postcode: ",p
           
        
        for up in unique_postcodes:
            up = up.strip()
            print "Processing postcode: ", up

            # Fetch the temperature data from the API 
            data = fetch_temp_data(up)

            if data == None:
                # Error messages should already be printed
                continue

            # Process the data 
            for day in data:
               
                # Get the reading date
                reading_date = day['date']

                # Data is returned as 3 hour blocks e.g. 9 to 12
                for threeHourWindow in day['hourly']:
                        
                    # Get time of reading and add a leading zero
                    reading_time = int(threeHourWindow['time']) / 100
                    if int(reading_time) < 10:
                        reading_time = "0" + str(reading_time)

                    # Get the reading temperature
                    reading_temp = threeHourWindow['FeelsLikeC']

                    # Create a reading / update is
                    ts = datetime.datetime.strptime(reading_date+" "+str(reading_time), "%Y-%m-%d %H")

                    # Add reading for each sensor using this postcode
                    sensor_profiles = Sensor_profile.objects.filter(postcode__startswith=up)
                    for sensor_profile in sensor_profiles:
                        reading, created = SensorReading.objects.get_or_create(timestamp=ts, sensor=sensor_profile.sensor, channel=channel)
                        reading.value = reading_temp
                        reading.save()
                        print 'Created reading: '+reading_date+' '+str(reading_time)+':00 hours, value: '+reading_temp+'^C -- '+str(sensor_profile.sensor.name)

                    








