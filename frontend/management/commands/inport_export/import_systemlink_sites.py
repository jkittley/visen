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

from frontend.models import Sensor_profile

import selenium.webdriver as webdriver

# 
#  EXAMPLE:  python manage.py import_systemlink --startdate 11/11/14 --enddate 18/11/14
# 

class Command(BaseCommand):
    help = 'Populates the db from SystemLink'
    option_list = BaseCommand.option_list + (
     
        make_option('--slinkuser',
                    dest='slinkuser',
                    default="Alexa.spence@nottingham.ac.uk",
                    help='Username for account used to access System-Link'),
        make_option('--slinkpass',
                    dest='slinkpass',
                    default="bournehill",
                    help='Password for account used to access System-Link')
        )
    
   

    def handle(self, *args, **options):
        
        def cap(s, l):
            return s if len(s)<=l else s[0:l-3]+'...'

        sensorsData  = {}
        channelNames = []

        firefox = webdriver.Firefox()
        firefox.get("http://www.systems-link.co.uk/webreports3/default.aspx")
        
        username = firefox.find_element_by_id("ctl00_ctl00_contentBody_UserNameInput_I")
        password = firefox.find_element_by_id("ctl00_ctl00_contentBody_PasswordInput_I")

        username.send_keys(options['slinkuser'])
        password.send_keys(options['slinkpass'])

        element = firefox.find_element_by_id("ctl00_ctl00_contentBody_LogOnButton_CD")
        element.click()


        # --------------------------------------------------------------------------------
        #  NOW WE ARE LOGGED IN
        # --------------------------------------------------------------------------------

        html     = firefox.page_source       
        soup     = BeautifulSoup(html)
        numpages = int(soup.find(id='ctl00_contentBody_ctl00_grdSiteList_grid_DXPagerBottom').find_all("a")[-1].get_text())
        
        if numpages == 0:
            print "No pages of sites seen."
            return

        print str(numpages)+" pages of sites seen."

        # A list of all contact ids
        contactids = []

        # For each page of sites
        for pnum in range(0,numpages):

            print "Openning page: ", pnum
            firefox.execute_script("aspxGVPagerOnClick('ctl00_contentBody_ctl00_grdSiteList_grid','PN"+str(pnum)+"');")
            time.sleep(5)

            # For each site on current page
            for i in range(0,25):
                griddata = firefox.execute_script("return grid.keys["+str(i)+"]")
                if griddata:
                    contactid = int(griddata)
                # Add to master list if not already present
                if not contactid in contactids:
                    if contactid:
                        contactids.append(contactid)
                        print "Added contact ID: ", contactid

            # Advance to next page in list
            print "Sites found so far: ", len(contactids)
            

        print "--------------------------------------------------"
        print "Sites found: ", len(contactids)
        print "--------------------------------------------------"
        
        # For each contact ID get the site information
        for site_contact_id in contactids:
        # for site_contact_id in [735,1217]:

            # Create a data object for eac site
            sensorsData[site_contact_id] = {}
            
            # Fetch the site details page
            firefox.get("http://www.systems-link.co.uk/webreports3/datasetlist.aspx?contactid="+str(site_contact_id))

            # Get the name and address
            sensorsData[site_contact_id]['sitename'] = str(firefox.find_element_by_id("ctl00_contentBody_siteDetails_NameValue").text)
            sensorsData[site_contact_id]['address']  = str(firefox.find_element_by_id("ctl00_contentBody_siteDetails_AddressValue").text)
            sensorsData[site_contact_id]['postcode'] = str(sensorsData[site_contact_id]['address'].split(",")[-1].strip())

            # Get the list of services they have data for e.g. Electricity, Gas...
            html   = firefox.page_source       
            soup   = BeautifulSoup(html)
            table  = soup.find("table",{"id": "ctl00_contentBody_grdDataSets_grid_DXMainTable"}).find('tbody').find_all('tr')
            sensorsData[site_contact_id]['channels'] = []
            # Loop through each row of the table
            for row in table[9:]:
                cells = row.find_all("td")
                etype = cap(str(cells[0].get_text()),32)
                if etype:
                    # Does it already exist in the channels list?
                    if not etype in sensorsData[site_contact_id]['channels']:
                        # Add to channel list
                        sensorsData[site_contact_id]['channels'].append(str(etype))
                        # Add to unique channels list
                        if not etype in channelNames:
                            channelNames.append(str(etype))
        
        # Close the session
        firefox.quit();

        # --------------------------------------------------------------------------------
        #  NOW WE HAVE A LIST OF SENSORS (SITES) AND CHANNELS (ENERGY SUPPLY DATA SOURCES)
        # --------------------------------------------------------------------------------
        # print sensorsData
        # print channelNames


        # Create channels that dont already exist
        for channel_name in channelNames:
            try:
                c = Channel.objects.all().get(name=channel_name)
            except:
                channel = Channel(name=channel_name, reading_frequency=1800, unit='Units')
                channel.save()
                print "created new channel: " + channel_name


        # Fetch the superuser to create sensors
        defaultuser  = User.objects.get(pk=1)

        # Create temperature channel 
        temp_ch_name = 'Temp (Feels like)'
        try:
            tempChannel = Channel.objects.all().get(name=temp_ch_name)
        except:
            tempChannel = Channel(name=temp_ch_name, reading_frequency=10800, unit='^C')
            tempChannel.save()
            print "Created temperature channel: "+temp_ch_name

        # Create sensors that don't exist
        for site_contact_id in sensorsData:
            sd = sensorsData[site_contact_id]
            
            # Add the temp channel to all
            sd['channels'].append(temp_ch_name)

            # Load or create the sensor
            try:
                sensor = Sensor.objects.all().get(mac=site_contact_id)
            except:
                sensor = Sensor(name=cap(sd['sitename'],30), mac=site_contact_id, user=defaultuser)
                sensor.save()
                print "created new sensor: " + str(site_contact_id)

            # Add all the channels
            for ch in sd['channels']:
                channel = None
                try:
                    channel = Channel.objects.all().get(name=ch)
                    sensor.channels.add(channel)
                    print "Added '"+ch+"'' channel to sensor: " + str(site_contact_id)
                except:
                    print "Failed to add '"+ch+"'' channel to sensor: " + str(site_contact_id)

            # Create the channels profile
            try:
                profile = Sensor.objects.all().get(sensor=sensor)
            except:
                profile = Sensor_profile(sensor=sensor, longname=cap(sd['sitename'],200) ,address=sd['address'], postcode=sd['postcode'])
                profile.save()
                print "created new sensor profile: " + str(site_contact_id)
         
             
                
            


        









                    