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
        #  Bar Chart - Dasys Of Month Total Usage
        # --------------------------------------------------------------------------------
        year = 2014
        maxcount = 2
        counter  = 0
        seasons = get_season_dates(year)
        channel_gas  = Channel.objects.all().get(name='Gas')  
        channel_elec = Channel.objects.all().get(name='Electricity')  
        channel_open = Channel.objects.all().get(name__icontains='Opening') 

        for site_type in ["depot","library","leisure"]:
            for channel in [channel_gas, channel_elec]:

                # Get all the sensors of the site type
                profiles = Sensor_profile.objects.filter(longname__icontains=site_type)
                master = []
                labels = []

                # Loop through each profile 
                for profile in profiles:

                    if channel not in profile.sensor.channels.all():
                        continue

                    # Create plot
                    fig = plt.figure(figsize=(14, 8))

                    fig.suptitle(site_type.capitalize()+' '+channel.name.capitalize()+' '+profile.longname+' (Total Day Usage / Hours Open)' , fontsize=14, fontweight='bold')
                    
                    fig.subplots_adjust(wspace=0.4, hspace=0.4)
       
                    print profile.sensor.mac + ' ' + profile.sensor.name

                    readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel)
                    open_hrs = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel_open)

                    data = {}
                    ohrs = {}
                    for i in range(1,13):
                        data[i] = { 'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0 }
                        ohrs[i] = { 'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0 }
                    
                    # Work out total reading for day in month
                    for r in readings:
                        data[int(r.timestamp.strftime('%m'))][r.timestamp.strftime('%a')] += r.value

                    # Work out total number of hours open

                    for o in open_hrs:
                        ohrs[int(o.timestamp.strftime('%m'))][o.timestamp.strftime('%a')] += (o.value * 0.5)
                      

                    # Work out total reading / hours open
                    for m in data:
                        for d in data[m]:
                            if ohrs[m][d] > 0:
                                data[m][d] = data[m][d] / ohrs[m][d]


                    bottom=0
                    width=10
                    days   = [ 'Sun','Mon','Tue','Wed','Thu','Fri','Sat' ]
                    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
                    
                    for month in data:
                        tmpdata = []
                        ax1 = None
                        ax1 = fig.add_subplot(2,6,month)
                        
                        for day in days:
                            tmpdata.append(data[month][day])
                        
                        cms = np.array(tmpdata)
                        ax1.set_title(months[month-1])
                        ax1.bar(range(0,7), cms, bottom=bottom)
                        ax1.set_xticklabels(days, rotation=90,  fontsize=10)  
                        ax1.tick_params(axis='y', labelsize=10)
                        
                        if month==1 or month==7:
                            ax1.set_ylabel('Total Readings This Day - This Month',  fontsize=10)
                    
                    directory = 'zzz_images/bar/days_of_month_divided_by_opening/'
                    filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+' '+profile.longname+'.png'
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    fig.savefig(directory+filename, bbox_inches='tight')
                    plt.clf()

                

        # # --------------------------------------------------------------------------------
        # #  Bar Chart - Dasys Of Month Total Usage
        # # --------------------------------------------------------------------------------
        # year = 2014
        # maxcount = 2
        # counter  = 0
        # seasons = get_season_dates(year)
        # channel_gas  = Channel.objects.all().get(name='Gas')  
        # channel_elec = Channel.objects.all().get(name='Electricity')  
        # channel_temp = Channel.objects.all().get(name='Temp (Feels like)')  

        # # plt.title(site_type.capitalize()+' '+channel.name.capitalize()+' '+profile.sensor.name.capitalize())
                    
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

        #             # Create plot
        #             fig = plt.figure(figsize=(14, 8))

                    
        #             fig.suptitle(site_type.capitalize()+' '+channel.name.capitalize()+' '+profile.longname , fontsize=14, fontweight='bold')
                    
        #             fig.subplots_adjust(wspace=0.4, hspace=0.4)
       
        #             print profile.sensor.mac + ' ' + profile.sensor.name

        #             readings = SensorReading.objects.filter(sensor=profile.sensor, timestamp__range=(seasons['winter']['start'], seasons['autumn']['end']), channel=channel)

        #             data = {}
        #             for i in range(1,13):
        #                 data[i] = { 'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0 }
        
        #             for r in readings:
        #                 data[int(r.timestamp.strftime('%m'))][r.timestamp.strftime('%a')] += r.value
                      

        #             bottom=0
        #             width=10
        #             days   = [ 'Sun','Mon','Tue','Wed','Thu','Fri','Sat' ]
        #             months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
                    
        #             for month in data:
        #                 tmpdata = []
        #                 ax1 = None
        #                 ax1 = fig.add_subplot(2,6,month)
                        
        #                 for day in days:
        #                     tmpdata.append(data[month][day])
                        
        #                 cms = np.array(tmpdata)
        #                 ax1.set_title(months[month-1])
        #                 ax1.bar(range(0,7), cms, bottom=bottom)
        #                 ax1.set_xticklabels(days, rotation=90,  fontsize=10)  
        #                 ax1.tick_params(axis='y', labelsize=10)
                        
        #                 if month==1 or month==7:
        #                     ax1.set_ylabel('Total Readings This Day - This Month',  fontsize=10)
                    
        #             directory = 'zzz_images/bar/days_of_month/'
        #             filename  = 'winter'+str(year-1)+'_to_autumn_'+str(year)+'_'+site_type+' '+channel.name+' '+profile.longname+'.png'
        #             if not os.path.exists(directory):
        #                 os.makedirs(directory)

        #             fig.savefig(directory+filename, bbox_inches='tight')
        #             plt.clf()
        


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







        
  

