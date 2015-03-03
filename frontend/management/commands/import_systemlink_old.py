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

# 
#  ECAMPLE:  python manage.py import_systemlink --startdate 11/11/14 --enddate 18/11/14 --user jacob --site 735 --datatype Gas
# 

class Command(BaseCommand):
    help = 'Populates the db from SystemLink'
    option_list = BaseCommand.option_list + (
        make_option('--user',
                    dest='user',
                    default=None,
                    help='Select a specific user'),
        make_option('--startdate',
                    dest='startdate',
                    default=None,
                    help='Select a specific start date'),
        make_option('--enddate',
                    dest='enddate',
                    default=None,
                    help='Select a specific end date'),
        make_option('--site',
                    dest='site',
                    default=None,
                    help='Site to import'),
        make_option('--datatype',
                    dest='datatype',
                    default=None,
                    help='Data type to import'),
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
            startdate = datetime.date.today()
        else:
            startdate = datetime.datetime.strptime(options['startdate'], "%d/%m/%y").date()

        if options['enddate'] == None:
            enddate = datetime.date.today()
        else:
            enddate = datetime.datetime.strptime(options['enddate'], "%d/%m/%y").date()

        if options['site'] == None:
            print "Please specify a site"
            return

        if options['datatype'] == None:
            print "Please specify a data type to import"
            return

        if options['user'] == None:
            print "Please specify at least one user to import as using --user"
            return

        if options['slinkuser'] == None:
            print "Please specify a username for the System-Link account you wish to login as --slinkuser"
            return

        if options['slinkpass'] == None:
            print "Please specify a password for the System-Link account you wish to login as --slinkpass"
            return
      
        # Download Data
        br = mechanize.Browser()
        cj = br.set_cookiejar(cookielib.LWPCookieJar())
        br.set_handle_equiv(True)
        br.set_handle_gzip(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        #br.set_proxies({ "http" : "127.0.0.1:8080"})
        # Follows refresh 0 but not hangs on refresh > 0
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        # User-Agent (this is cheating, ok?)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

        # Connect to system link
        r = br.open('http://www.systems-link.co.uk/webreports3/default.aspx')
        if br.title().strip() != "Login":
            print "Failed to login to connect to server"
            return
        else:
            
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
            else:

                print "Logged in"

                # Fetch data from profile downloader
                r = br.open('http://www.systems-link.co.uk/webreports3/ProfileDownload.aspx?site=' + str(options['site']))
                br.select_form(name="aspnetForm")
                form = br.form
                form.set_all_readonly(False)

                sst = time.mktime( startdate.timetuple() )
                sft = startdate.strftime('%d/%m/%Y')
                est = time.mktime( enddate.timetuple() )
                eft = enddate.strftime('%d/%m/%Y')

                startstamp  = str(int(sst) * 1000)
                starttime   = sft
                endstamp    = str(int(est) * 1000)
                endtime     = eft
                form['ctl00_contentBody_UtilityList_VI']    = options['datatype'].capitalize()
                form['ctl00$contentBody$UtilityList']       = options['datatype'].capitalize()
                form['ctl00$contentBody$UtilityList$DDD$L'] = options['datatype'].capitalize()
                form['ctl00_contentBody_DateEditStart_Raw'] = startstamp
                form['ctl00_contentBody_DateEditEnd_Raw']   = endstamp
                    
                br.submit()

                csvdata = br.response().read();

        # if (True):
        #     if (True):
        #         csvdata = open("/Users/jacob/Dropbox/dev/uni/COMP3020/EXTRACT/temp.csv", 'rU')

                rows    = csv.DictReader(StringIO.StringIO(csvdata))

                user    = User.objects.get(username=options['user'])
                sensor  = Sensor.objects.get(mac=options['site'], user=user)
                channel = Channel.objects.get(name=options['datatype'])

                if (user == None):
                    print "Failed to find user:", options['user']
                    return
                if (sensor == None):
                    print "Failed to find sensor for stie:", options['site']
                    return
                if (channel == None):
                    print "Failed to find channel for data type:", options['datatype']
                    return

                rowcount = 1

                # Loop through the rows in the csv data
                for row in rows:
                    
                    print "prcessing row ", rowcount
                    rowcount = rowcount + 1
                    
                    reading_date  = None
                    reading_value = None

                    # Get the date first
                    for k in row:
                        if (k.strip().lower()=="date"):
                            reading_date = row[k].strip().lower()

                    # If the date is missing skip row
                    if (reading_date == None):
                        print "Failed to locate date"
                        continue

                    # Now go through all the other cols in this row
                    colcount = 0
                    for k in row:
                        
                        rowval       = row[k]
                        colname      = k.strip().lower()
                        reading_time = colname[:5]
                        colcount     = colcount + 1

                        try:
                            # Fix stupid csv title
                            if (reading_time == "24:00"):
                                reading_time = "23:59"
                            ts = datetime.datetime.strptime(reading_date+" "+reading_time, "%d/%m/%Y %H:%M")
                            reading, created = SensorReading.objects.get_or_create(timestamp=ts, sensor=sensor, channel=channel)
                            reading.value = rowval.strip()
                            reading.save()
                            
                            print colcount, "- "+reading_date+" "+reading_time+", sensor (site) "+options['site']+", channel(datatype) "+options['datatype']+", Reading Value "+rowval.strip()
                            # except:
                                # print "Row failed to import", row     
                        except:
                            print colcount, "- Column title:", colname, "not a valid time format e.g. 23:30"

                          
                    