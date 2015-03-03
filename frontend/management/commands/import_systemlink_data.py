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
import shutil
import pprint
import json

# 
#  EXAMPLE:  python manage.py import_systemlink_data --startdate 11/11/14 --enddate 18/11/14
# 

class Command(BaseCommand):
    help = 'Populates the db from SystemLink'
    option_list = BaseCommand.option_list + (
       
        make_option('--startdate',
                    dest='startdate',
                    default=None,
                    help='Select a specific start date'),
        make_option('--enddate',
                    dest='enddate',
                    default=None,
                    help='Select a specific end date'),
        make_option('--slinkuser',
                    dest='slinkuser',
                    default="Alexa.spence@nottingham.ac.uk",
                    help='Username for account used to access System-Link'),
        make_option('--slinkpass',
                    dest='slinkpass',
                    default="bournehill",
                    help='Password for account used to access System-Link'),
        )
    



    def handle(self, *args, **options):
        if options['startdate'] == None:
            print "You must specify a start date"
            return

        if options['enddate'] == None:
            print "You must specify an end date"
            return

        # Clear the screen
        for i in range(1,30):
             print " "

        startdate = datetime.datetime.strptime(options['startdate'], "%d/%m/%y").date()
        enddate   = datetime.datetime.strptime(options['enddate'], "%d/%m/%y").date()
      
        # Download Data
        br = mechanize.Browser()
        cj = br.set_cookiejar(cookielib.LWPCookieJar())
        br.set_handle_equiv(True)
        br.set_handle_gzip(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

        # Connect to system link
        r = br.open('http://www.systems-link.co.uk/webreports3/default.aspx')
        if br.title().strip() != "Login":
            print "Failed to login to connect to server"
            return
        
            
        print "Connected to server, logging in"

        # Login
        br.select_form(nr=0)
        br.form['ctl00$ctl00$contentBody$UserNameInput']=options['slinkuser']
        br.form['ctl00$ctl00$contentBody$PasswordInput']=options['slinkpass']
        br.submit()

        # Check if logged in
        if br.title().strip() != "Site List":
            print "Failed to login to system link using user:", options['user']
            return
            
        print "Logged in"

        # 
        # Loop through all sensors and download all channels
        # 

        sensors     = Sensor.objects.all()
        user        = User.objects.get(pk=1)
        
        sensorcount = 0
        for sensor in sensors:
            sensorcount = sensorcount + 1
        current_sensor = 0;

        # Limit number of sensors to process
        sensor_limit = sensorcount
        # sensor_limit = 5

        # wait = True

        for sensor in sensors:

            # if sensor.mac == '393':
            #     wait = False

            # if wait:
            #     continue

            if sensor_limit == current_sensor:
                print "---------------------------------------------"
                print "Sensor limit reached ("+str(sensor_limit)+")"
                print "---------------------------------------------"
                return

            current_sensor = current_sensor + 1
            print " "
            print "---------------------------------------------"
            print "Processing sensor " + str(current_sensor) + " of " + str(sensorcount) + ". Sensor id: " + str(sensor.mac)
            print "---------------------------------------------"

            for channel in sensor.channels.all():

                if channel.name.startswith("Temp"):
                    break

                print " "
                print "~ Processing channel: ",channel

                max_attempts    = 5
                current_attempt = 1
                while current_attempt <= max_attempts:  

                    pagedata = None

                    print "~ Fetching channel data: " + channel.name + ". Attempt " + str(current_attempt) + " of " + str(max_attempts)

                    # Open the csv download page
                    try:
                        url  = 'http://www.systems-link.co.uk/webreports3/ProfileDownload.aspx?site=' + str(sensor.mac)
                        r    = br.open(url)
                    except:
                        continue

                    br.select_form(name="aspnetForm")
                    form = br.form
                    form.set_all_readonly(False)
                        
                    # Fill in the form
                    sst = time.mktime( startdate.timetuple() )
                    sft = startdate.strftime('%d/%m/%Y')
                    est = time.mktime( enddate.timetuple() )
                    eft = enddate.strftime('%d/%m/%Y')
                    startstamp  = str(int(sst) * 1000)
                    starttime   = sft
                    endstamp    = str(int(est) * 1000)
                    endtime     = eft
                    form['ctl00_contentBody_UtilityList_VI']    = channel.name
                    form['ctl00$contentBody$UtilityList']       = channel.name
                    form['ctl00$contentBody$UtilityList$DDD$L'] = channel.name
                    form['ctl00_contentBody_DateEditStart_Raw'] = startstamp
                    form['ctl00_contentBody_DateEditEnd_Raw']   = endstamp
                    br.submit()

                    # Get the CSV data returned
                    pagedata = br.response().read();

                    if current_attempt == max_attempts:
                        print "~ Maximum download attempt reached for: " + str(sensor.mac)
                        pagedata = None
                        break

                    if pagedata.startswith("Meter Id"):
                        print "~ Data downloaded for sensor: " + str(sensor.mac) + " channel: " + str(channel.name)
                        break
                    
                    # If the data download has failed, try again in x seconds
                    time.sleep(10)

                    # Increment the attempt number
                    current_attempt = current_attempt + 1


                # Once multiple download attempts have been made
                if pagedata == None:
                    print "~ Failed to download " + str(sensor.mac) +"s data"
                    break
            
                # Parse the CSV data - Rows is a dict where the key (k) is the column name from row 1
                rows     = csv.DictReader(StringIO.StringIO(pagedata))
                
                print "~ Processing downloaded CSV file "

                rows_count        = 0
                rows_added_count  = 0
                rows_failed_count = 0
                readings_count    = 0

                import_object = { "readings": [] }

                # Loop through the rows in the csv data    
                for row in rows:
                    
                    rows_count   += 1      
                    reading_date  = None
                    reading_value = None

                    # Get the date 
                    for k in row:
                        if k != None:
                            if (k.strip().lower()=="date"):
                                reading_date = row[k].strip().lower()

                    # If the date is missing skip row
                    if (reading_date == None):
                        rows_failed_count += 1 
                        
                    else:

                        # Now go through all the other cols in this row
                        colcount = 0
                        prev_h   = None
                        prev_m   = None

                        for k in row:
                            if k != None and k.strip().lower()!="date" and k.strip().lower()!="meter id":
                                rowval       = float(row[k].strip())
                                colname      = k.strip().lower()
                                reading_time = colname[:5]
                                colcount    += 1
                                h           = int(colname[:2])
                                m           = int(colname[3:5])
                                diff        = None

                                # Reading times are marked at the end of a session so the period
                                # between 23:30 and 00:00 is marked as 24:00! So this next bit fixes this
                                if h == 24:
                                    h = 23
                                    m = 59

                                # Calculate period since last reading
                                if prev_h:
                                    a = datetime.datetime(2013,1,1,prev_h,prev_m,00)
                                    b = datetime.datetime(2013,1,1,h,m,00)
                                    diff = (b-a).total_seconds()
                                
                                prev_h = h
                                prev_m = m

                                import_object['readings'].append({ 'date':reading_date, 'hour':h, 'min':m, 'val':rowval, 'secs_since_last_reading':diff })

                                
                                ts = datetime.datetime.strptime(reading_date+" "+str(h)+":"+str(m), "%d/%m/%Y %H:%M")
                                reading, created = SensorReading.objects.get_or_create(timestamp=ts, sensor=sensor, channel=channel)
                                reading.value = rowval
                                reading.save()
                                readings_count +=1

                            rows_added_count += 1
                                  

                print "No. Rows: ",rows_count
                print "No. Rows read successfully: ",rows_added_count
                print "No. Rows failed: ",rows_failed_count
                print "No. Readings: ",readings_count
                # pprint.pprint(import_object)



                            