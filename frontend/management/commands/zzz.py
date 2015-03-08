#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
import datetime, os
from frontend.models import *
import matplotlib.pyplot as plt
import numpy as np

class Command(BaseCommand):
    
    def handle(self, *args, **options):

        

        # --------------------------------------------------------------------------------
        #  Rate Of Change
        # --------------------------------------------------------------------------------
        # year = 2014
        # maxcount = 1
        # counter  = 0
        # seasons = get_season_dates(year)
        # channel_gas  = Channel.objects.all().get(name='Gas')  
        # channel_elec = Channel.objects.all().get(name='Electricity')  
        # channel_temp = Channel.objects.all().get(name='Temp (Feels like)')  


        # for site_type in ["depot","library","leisure"]:
        #     for channel in [channel_gas, channel_elec]:

        #         # Get all the sensors of the site type
        #         profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
        #         master = []
        #         labels = []

        #         # Loop through each profile 
        #         for profile in profiles:

        #             if channel not in profile.sensor.channels.all():
        #                 continue

        #             counter += 1
        #             if counter > maxcount:
        #                 return
       
        #             print profile.sensor.mac + ' ' + profile.sensor.name

        #             readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel)

        #             tmpA = []
        #             for r in readings:
        #                 if r.value > 1:
        #                     tmpA.append(r.value)

        #             tmpB = np.diff(tmpA)

        #             ply.xticks()
                    
        #             plt.title(site_type.capitalize()+' '+channel.name.capitalize()+' '+profile.sensor.name)
        #             plt.hist(tmpB, bins=20, normed=True, cumulative=False)
                    
        #             directory = 'zzz_images/histogram/RoC_Yearly/'
        #             filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+'.png'
                    
        #             if not os.path.exists(directory):
        #                 os.makedirs(directory)

        #             plt.savefig(directory+filename, bbox_inches='tight')

        #             print "--------------"



        # # --------------------------------------------------------------------------------
        # #  Rate Of Change
        # # --------------------------------------------------------------------------------
        # year = 2014
        # maxcount = 99999999999
        # counter  = 0
        # seasons = get_season_dates(year)
        # channel_gas  = Channel.objects.all().get(name='Gas')  
        # channel_elec = Channel.objects.all().get(name='Electricity')  
        # channel_temp = Channel.objects.all().get(name='Temp (Feels like)')  


        # for site_type in ["depot","library","leisure"]:
        #     for channel in [channel_gas, channel_elec]:

        #         # Get all the sensors of the site type
        #         profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
        #         master = []
        #         labels = []

        #         # Loop through each profile 
        #         for profile in profiles:

        #             if channel not in profile.sensor.channels.all():
        #                 continue

        #             counter += 1
        #             if counter > maxcount:
        #                 return
       
        #             print profile.sensor.mac + ' ' + profile.sensor.name

        #             readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel)

        #             data = { 
        #                 'Mon': [],
        #                 'Tue': [],
        #                 'Wed': [],
        #                 'Thu': [],
        #                 'Fri': [],
        #                 'Sat': [],
        #                 'Sun': [],
        #             }
        
        #             for r in readings:
        #                 data[r.timestamp.strftime('%a')].append(r.value)
                      

        #             for day in [ 'Mon','Tue','Wed','Thu','Fri','Sat','Sun' ]:
        #                 tmpdata = data[day]
        #                 labels.append(day+' '+profile.sensor.mac)
        #                 master.append(list( np.diff( np.array( tmpdata )) ))

        #         # Create the boxplot
        #         number_results       = counter
        #         num_cols_per_sensor  = 10
        #         scale                = 1

        #         # Create a figure instance
        #         fig = plt.figure(1, figsize=(number_results*scale*num_cols_per_sensor, 6))

        #         # Create an axes instance
        #         ax = fig.add_subplot(111)

        #         directory = 'zzz_images/box/Daily_RoC/'
        #         filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+'.png'
                
        #         if not os.path.exists(directory):
        #             os.makedirs(directory)

        #         print directory+filename
        #         ax.set_title(directory+filename)

        #         # Create the boxplot
        #         ax.boxplot(master)

        #         # Add labels
        #         ax.set_xticklabels(labels, rotation=90)   
            
        #         fig.savefig(directory+filename, bbox_inches='tight')

        #         plt.clf()
                
        #         print "--------------"


        # --------------------------------------------------------------------------------
        #  Rate Of Change - Seasonal
        # --------------------------------------------------------------------------------
        # year = 2014
        # maxcount = 99999999999
        # counter  = 0
        # seasons = get_season_dates(year)
        # channel_gas  = Channel.objects.all().get(name='Gas')  
        # channel_elec = Channel.objects.all().get(name='Electricity')  
        # channel_temp = Channel.objects.all().get(name='Temp (Feels like)')  


        # for site_type in ["depot","library","leisure"]:
        #     for channel in [channel_gas, channel_elec]:

        #         # Get all the sensors of the site type
        #         profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
        #         master = []
        #         labels = []

        #         # Loop through each profile 
        #         for profile in profiles:

        #             if channel not in profile.sensor.channels.all():
        #                 continue

        #             counter += 1
        #             if counter > maxcount:
        #                 return
       
        #             print profile.sensor.mac + ' ' + profile.sensor.name

        #             winter_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['winter']['end']), channel=channel)
        #             spring_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['spring']['start'], seasons['spring']['end']), channel=channel)
        #             summer_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['summer']['start'], seasons['summer']['end']), channel=channel)
        #             autumn_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['autumn']['start'], seasons['autumn']['end']), channel=channel)

        #             data = { 
        #                 'spring': {},
        #                 'summer': {},
        #                 'autumn': {},
        #                 'winter': {},
        #             }

        #             for season_readings in [['winter',winter_readings], ['spring',spring_readings], ['summer',summer_readings], ['autumn',autumn_readings]]: 
        #                 for r in season_readings[1]:
        #                     try:  
        #                         data[season_readings[0]][r.timestamp.strftime('%Y-%m-%d %H:%M')] += r.value
        #                     except KeyError:
        #                         data[season_readings[0]][r.timestamp.strftime('%Y-%m-%d %H:%M')]  = r.value

        #             for season in data:
        #                 tmpdata = data[season]
        #                 if (len(tmpdata.values())>0):
        #                     labels.append(season+' '+profile.sensor.mac)
        #                     master.append(list( np.diff( np.array( tmpdata.values() )) ))
                    
        #         # Create the boxplot
        #         number_results       = counter
        #         num_cols_per_sensor  = 10
        #         scale                = 1

        #         # Create a figure instance
        #         fig = plt.figure(1, figsize=(number_results*scale*num_cols_per_sensor, 6))

        #         # Create an axes instance
        #         ax = fig.add_subplot(111)

        #         directory = 'zzz_images/box/Seasonal_RoC/'
        #         filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+'.png'
                
        #         if not os.path.exists(directory):
        #             os.makedirs(directory)

        #         print directory+filename
        #         ax.set_title(directory+filename)

        #         # Create the boxplot
        #         ax.boxplot(master)

        #         # Add labels
        #         ax.set_xticklabels(labels, rotation=90)   
            
        #         fig.savefig(directory+filename, bbox_inches='tight')

        #         plt.clf()
                
        #         print "--------------"



        # # --------------------------------------------------------------------------------
        # #  Seasonal Day Totals
        # # --------------------------------------------------------------------------------
        # year = 2014
        # maxcount = 99999999999
        # counter  = 0
        # seasons = get_season_dates(year)
        # channel_gas  = Channel.objects.all().get(name='Gas')  
        # channel_elec = Channel.objects.all().get(name='Electricity')  
        # channel_temp = Channel.objects.all().get(name='Temp (Feels like)')  


        # for site_type in ["depot","library","leisure"]:
        #     for channel in [channel_gas, channel_elec]:

        #         # Get all the sensors of the site type
        #         profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
        #         master = []
        #         labels = []

        #         # Loop through each profile 
        #         for profile in profiles:

        #             if channel not in profile.sensor.channels.all():
        #                 continue

        #             counter += 1
        #             if counter > maxcount:
        #                 return
       
        #             print profile.sensor.mac + ' ' + profile.sensor.name

        #             winter_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['winter']['end']), channel=channel)
        #             spring_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['spring']['start'], seasons['spring']['end']), channel=channel)
        #             summer_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['summer']['start'], seasons['summer']['end']), channel=channel)
        #             autumn_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['autumn']['start'], seasons['autumn']['end']), channel=channel)
                    
        #             data = { 
        #                 'spring': {},
        #                 'summer': {},
        #                 'autumn': {},
        #                 'winter': {},
        #             }

        #             for season_readings in [['winter',winter_readings], ['spring',spring_readings], ['summer',summer_readings], ['autumn',autumn_readings]]: 
        #                 for r in season_readings[1]:
        #                     try:  
        #                         data[season_readings[0]][r.timestamp.strftime('%Y-%m-%d')] += r.value
        #                     except KeyError:
        #                         data[season_readings[0]][r.timestamp.strftime('%Y-%m-%d')]  = r.value

        #             for season in data:
        #                 tmpdata = data[season]
        #                 if (len(tmpdata.values())>0):
        #                     labels.append(season+' '+profile.sensor.mac)
        #                     master.append(tmpdata.values())


        #         # Create the boxplot
        #         number_results       = counter
        #         num_cols_per_sensor  = 10
        #         scale                = 1

        #         # Create a figure instance
        #         fig = plt.figure(1, figsize=(number_results*scale*num_cols_per_sensor, 6))

        #         # Create an axes instance
        #         ax = fig.add_subplot(111)

        #         directory = 'zzz_images/box/Seasonal_Day_Totals/'
        #         filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+'.png'
                
        #         if not os.path.exists(directory):
        #             os.makedirs(directory)

        #         print directory+filename
        #         ax.set_title(directory+filename)

        #         # Create the boxplot
        #         ax.boxplot(master)

        #         # Add labels
        #         ax.set_xticklabels(labels, rotation=90)   
            
        #         fig.savefig(directory+filename, bbox_inches='tight')

        #         plt.clf()
                
        #         print "--------------"


        # # --------------------------------------------------------------------------------
        # #  Seasonal Day Totals - Weekend Vs Weekday
        # # --------------------------------------------------------------------------------
        
        # year = 2014
        # maxcount = 599999999999999999
        # counter  = 0
        # seasons = get_season_dates(year)
        # channel_gas  = Channel.objects.all().get(name='Gas')  
        # channel_elec = Channel.objects.all().get(name='Electricity')  
        # channel_temp = Channel.objects.all().get(name='Temp (Feels like)')  


        # for site_type in ["depot","library","leisure"]:
        #     for channel in [channel_gas, channel_elec]:

        #         # Get all the sensors of the site type
        #         profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
        #         master = []
        #         labels = []

        #         # Loop through each profile 
        #         for profile in profiles:

        #             if channel not in profile.sensor.channels.all():
        #                 continue

        #             counter += 1
        #             if counter > maxcount:
        #                 return
       
        #             print profile.sensor.mac + ' ' + profile.sensor.name

        #             winter_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['winter']['end']), channel=channel)
        #             spring_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['spring']['start'], seasons['spring']['end']), channel=channel)
        #             summer_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['summer']['start'], seasons['summer']['end']), channel=channel)
        #             autumn_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['autumn']['start'], seasons['autumn']['end']), channel=channel)
                    
        #             data = { 
        #                 'spring': { 'wend':{}, 'wday':{} },
        #                 'summer': { 'wend':{}, 'wday':{} },
        #                 'autumn': { 'wend':{}, 'wday':{} },
        #                 'winter': { 'wend':{}, 'wday':{} },
        #             }

        #             for season_readings in [['winter',winter_readings], ['spring',spring_readings], ['summer',summer_readings], ['autumn',autumn_readings]]: 
        #                 for r in season_readings[1]:

        #                     if r.timestamp.isoweekday() >= 6:
        #                         daytype = 'wend'
        #                     else:
        #                         daytype = 'wday'

        #                     try:  
        #                         data[season_readings[0]][daytype][r.timestamp.strftime('%Y-%m-%d')] += r.value
        #                     except KeyError:
        #                         data[season_readings[0]][daytype][r.timestamp.strftime('%Y-%m-%d')]  = r.value

        #             for season in data:
        #                 for daytype in ['wend','wday']:
        #                     tmpdata = data[season][daytype]
        #                     if (len(tmpdata.values())>0):
        #                         labels.append(season+' '+daytype+' '+profile.sensor.mac)
        #                         master.append(tmpdata.values())


        #         # Create the boxplot
        #         number_results       = counter
        #         num_cols_per_sensor  = 10
        #         scale                = 1

        #         # Create a figure instance
        #         fig = plt.figure(1, figsize=(number_results*scale*num_cols_per_sensor, 6))

        #         # Create an axes instance
        #         ax = fig.add_subplot(111)

        #         directory = 'zzz_images/box/Seasonal_Day_Totals__Weekend_Vs_Weekday/'
        #         filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+'.png'
                
        #         if not os.path.exists(directory):
        #             os.makedirs(directory)

        #         print directory+filename
        #         ax.set_title(directory+filename)

        #         # Create the boxplot
        #         ax.boxplot(master)

        #         # Add labels
        #         ax.set_xticklabels(labels, rotation=90)   

        #         fig.savefig(directory+filename, bbox_inches='tight')

        #         plt.clf()

        #         print "--------------"

        # # --------------------------------------------------------------------------------
        # #  Seasonal Day Totals - Weekend Vs Weekday
        # # --------------------------------------------------------------------------------
        
        # year = 2014
        # maxcount = 599999999999999999
        # counter  = 0
        # seasons = get_season_dates(year)
        # channel_gas  = Channel.objects.all().get(name='Gas')  
        # channel_elec = Channel.objects.all().get(name='Electricity')  
        # channel_temp = Channel.objects.all().get(name='Temp (Feels like)')  


        # for site_type in ["depot","library","leisure"]:
        #     for channel in [channel_gas, channel_elec]:

        #         # Get all the sensors of the site type
        #         profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
        #         master = []
        #         labels = []

        #         # Loop through each profile 
        #         for profile in profiles:

        #             if channel not in profile.sensor.channels.all():
        #                 continue

        #             counter += 1
        #             if counter > maxcount:
        #                 return
       
        #             print profile.sensor.mac + ' ' + profile.sensor.name

        #             season_readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel)
              
        #             data =  { 
        #                 'wend':{}, 
        #                 'wday':{} 
        #             }
                    
        #             for r in season_readings:

        #                 if r.timestamp.isoweekday() >= 6:
        #                     daytype = 'wend'
        #                 else:
        #                     daytype = 'wday'

        #                 try:  
        #                     data[daytype][r.timestamp.strftime('%Y-%m-%d')] += r.value
        #                 except KeyError:
        #                     data[daytype][r.timestamp.strftime('%Y-%m-%d')]  = r.value


        #             for daytype in ['wend','wday']:
        #                 tmpdata = data[daytype]
        #                 if (len(tmpdata.values())>0):
        #                     labels.append(daytype+' '+profile.sensor.mac)
        #                     master.append(tmpdata.values())



        #         number_results       = counter
        #         num_cols_per_sensor  = 10
        #         scale                = 1

        #         # Create a figure instance
        #         fig = plt.figure(1, figsize=(number_results*scale*num_cols_per_sensor, 6))

        #         # Create an axes instance
        #         ax = fig.add_subplot(111)

                
        #         directory = 'zzz_images/box/Full_Period_Weekday_Vs_Weekend/'
        #         filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+'.png'
                
        #         if not os.path.exists(directory):
        #             os.makedirs(directory)

        #         print directory+filename
        #         ax.set_title(directory+filename)

        #         # Create the boxplot
        #         ax.boxplot(master)

        #         # Add labels
        #         ax.set_xticklabels(labels, rotation=90)   

        #         fig.savefig(directory+filename, bbox_inches='tight')

        #         plt.clf()

        #         print "--------------"







        
  

