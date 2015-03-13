#encoding:UTF-8

from django.db import models
from django.db.models import Avg, Max, Min, Sum
from sd_store.models import Sensor, Channel, SensorReading
import django.contrib.auth
from datetime import datetime, date, timedelta
import numpy as np
import time, json

class Sensor_profile(models.Model):
    longname = models.CharField(max_length=200)
    sensor   = models.ForeignKey(Sensor, db_index=True)
    address  = models.CharField(max_length=200)
    postcode = models.CharField(max_length=20)
    lon      = models.FloatField(max_length=30, blank=True, null=True)
    lat      = models.FloatField(max_length=30, blank=True, null=True)
    def __unicode__(self):
        return 'Profile for: '+str(self.sensor.mac)

class Chart(models.Model):
    name       = models.CharField(max_length=255, unique=True)
    ref        = models.CharField(max_length=255, unique=True)
    min_inputs = models.IntegerField(default=1)
    max_inputs = models.IntegerField(default=1)
    default_settings = models.TextField(default='', blank=True)
    visin_config     = models.TextField(default='', blank=True)
    def __unicode__(self):
        return 'Chart: '+str(self.name)


class Visualisation(models.Model):
    name         = models.CharField(max_length=100)
    chart        = models.ForeignKey(Chart, db_index=True)
    cache        = models.TextField(default='', blank=True)
    settings     = models.TextField(default='', blank=True)
    processing   = models.TextField(default='', blank=True)
    group        = models.CharField(max_length=255, default='', blank=True)
    tier         = models.IntegerField(default=1)

    def __unicode__(self):
        return 'Visualisation: '+str(self.chart.name)+' of '+str(self.name)
    
    def get_all_channels(self):
        allins = VisInput.objects.all().filter(vis=self)
        unique_list = []
        for i in allins:
            if i.channel not in unique_list:
                unique_list.append(i.channel)
        return unique_list

    def get_all_inputs(self):
        return VisInput.objects.all().filter(vis=self)
       
    def get_input_tme_span(self):
        starts = VisInput.objects.all().filter(vis=self).order_by('period_start')
        ends   = VisInput.objects.all().filter(vis=self).order_by('period_end').reverse()
        if starts and ends:
            return [starts[0].period_start, ends[0].period_end]
        else:
            return [ None, None ]

    def get_settings(self):
        # Load defaults
        defaults = None
        try:
            defaults = json.loads(self.chart.default_settings)
        except:
            pass
        # Load vis customs
        custom   = None
        try:
            custom = json.loads(self.settings)
        except:
            pass
        # If we have defaults and customised settings then replace all defaults with customs
        if custom and defaults:
            for x in custom:
                defaults[x] = custom[x]
            return defaults
        # If we  only have custom settings then return those
        elif custom:
            return custom
        # If we only have the defaults then return them
        elif defaults:
            return defaults
        # If we have neither then return an empty dict
        else:
            return {}


class VisInput(models.Model):
    vis          = models.ForeignKey(Visualisation, db_index=True)
    name         = models.CharField(max_length=200, blank=True)
    sensor       = models.ForeignKey(Sensor, db_index=True)
    channel      = models.ForeignKey(Channel, db_index=True)
    period       = models.BooleanField(default=True)
    period_start = models.DateTimeField(auto_now_add=False)
    period_end   = models.DateTimeField(auto_now_add=False)
    interval     = models.IntegerField(default=-1)
    PP_NORMAL         = 0
    PP_RATE_OF_CHANGE = 1
    PPMODES = (
        (PP_NORMAL,  'Normal'),
        (PP_RATE_OF_CHANGE,   'Rate of Change')
    )
    preprocess   = models.IntegerField(default=0,  choices=PPMODES)
    TOTAL        = 0
    MEAN         = 1
    MIN          = 2
    MAX          = 3
    MEDIAN       = 4
    UPQ          = 5
    LOQ          = 6
    IQRSp        = 7
    MODES = (
        (TOTAL,  'Total'),
        (MEAN,   'Mean'),
        (MEDIAN, 'Median'),
        (MIN,    'Min'),
        (MAX,    'Max'),
        (UPQ,    'Upper Quartile'),
        (LOQ,    'Lower Quartile'),
        (IQRSp,  'Inter-Quartile Range Spread')
    )
    summode = models.IntegerField(max_length=2, choices=MODES, default=TOTAL)
    
    def __unicode__(self):
        return 'Input: '+str(self.name)+' [ '+str(self.sensor.name)+' '+str(self.channel.name)+' ]'

    def get_interval_mode(self, ts):
        string = ''
        if self.interval >= 86400:
            return ('days', ts.strftime('%d'))
        if self.interval >= 3600:
            return ('hours', ts.strftime('%H'))
        if self.interval >= 60:
            return ('minutes', ts.strftime('%M'))
        if self.interval > 0:
            return ('seconds', ts.strftime('%S'))
        if self.interval == -1:
            return ('daily', ts.strftime('%a'))
        if self.interval == -2:
            return ('weekly', ts.strftime('%Y-%m-%d'))
        if self.interval == -3:
            return ('monthly', ts.strftime('%Y %b'))
        if self.interval == -4:
            return ('seasonally', ts)
        if self.interval == -5:
            return ('anually', ts.strftime('%Y'))
        if self.interval == -6:
            return ('weekday_weekends', ts)
        if self.interval == -7:
            return ('seasonal_weekday_weekends', ts)
        if self.interval == -8:
            return ('all', ts)
        
      
    def get_readings(self):
        def roundTime(dt=None, roundTo=60):
            if dt == None : dt = datetime.datetime.now()
            seconds = (dt - dt.min).seconds
            # // is a floor division, not a comment on following line:
            rounding = (seconds+roundTo/2) // roundTo * roundTo
            return dt + timedelta(0,rounding-seconds,-dt.microsecond)

        #  Basic validation
        if self.interval == 0:
            return None
        if self.period_start >= self.period_end:
            return None
        if self.interval >= 0 and self.interval < self.channel.reading_frequency:
            return None

        # Use custom name for channel if set
        if self.name != '':
            tmpname = self.name
        else:
            tmpname = str(self.sensor.name)+' '+str(self.channel.name)

        # Create a series and add to output data
        output = { 'readings': [], 'num_readings': 0, 'name':tmpname }

        readings = SensorReading.objects.filter(sensor=self.sensor, channel=self.channel, timestamp__range=(self.period_start,self.period_end))
        interval_data = {}

        # Complie readings into lists, one each for interval period
        for r in readings:  

            # Set the key
            k = None

            # Seconds
            if self.interval > 0:
                k = roundTime(r.timestamp,self.interval)
            # Days
            elif self.interval == -1:
                k = datetime(r.timestamp.year, r.timestamp.month, r.timestamp.day, 0, 0)
            # Weeks
            elif self.interval == -2:
                tmp         = datetime(r.timestamp.year, r.timestamp.month, r.timestamp.day, 0, 0)
                day_of_week = tmp.weekday()
                k           = tmp - timedelta(days=day_of_week)
            # Months
            elif self.interval == -3:
                monthnum = r.timestamp.month
                k = datetime(r.timestamp.year, r.timestamp.month, 1, 0, 0)
            # Seasonal
            elif int(self.interval) == -4:
                k = which_season(r.timestamp)
                # k = datetime(r.timestamp.year, seasons[int(r.timestamp.month)-1], 1, 0, 0)
            # Annual
            elif self.interval == -5:
                k = r.timestamp.year
            # Weekdays
            elif self.interval == -6:
                tmp         = datetime(r.timestamp.year, r.timestamp.month, r.timestamp.day, 0, 0)
                day_of_week = tmp.weekday()
                if day_of_week in [1,2,3,4,5]:
                    k = 'weekday'
                else:
                    k = 'weekend'
            # Seasonal Weekdays / Weekends
            elif int(self.interval) == -7:
                tmp         = datetime(r.timestamp.year, r.timestamp.month, r.timestamp.day, 0, 0)
                day_of_week = tmp.weekday()
                seasons_names = ['winter','winter','spring','spring','spring','summer','summer','summer','autumn','autumn','autumn','winter']
                if day_of_week in [1,2,3,4,5]:
                    k = str(seasons_names[r.timestamp.month-1])+"_weekday"
                else:
                    k = str(seasons_names[r.timestamp.month-1])+"_weekend"
            # All
            elif int(self.interval) == -8:
                 k = 'all' 
            # Fail
            else:
                return None


            # Add an empty list for the key if it doesnt exist
            if k != None:
                if k not in interval_data:
                    interval_data[k] = []

                # Add the reading
                interval_data[k].append(r.value)


        # Preprocess
        if self.preprocess == self.PP_RATE_OF_CHANGE:
            for k in interval_data:
                interval_data[k] = list( np.diff( np.array( interval_data[k]) ))


        # Loop through each interval and calc a value to return based on the summode
        for ind in interval_data:
            if interval_data[ind]:
                a = np.array(interval_data[ind])
                
                stats = {
                    'mean':   np.mean(a),
                    'median': np.median(a),
                    'min':    np.min(a),
                    'max':    np.max(a),
                    'sum':    np.sum(a),
                    'upper_quartile':  np.percentile(a, 75),
                    'lower_quartile':  np.percentile(a, 25), 
                    'histogram': np.histogram(a, 20),
                }
               
                b = np.percentile(a, [75 ,25])
                stats['interquartile_range'] = list(b)
                # stats['interquartile_range_spread'] = ( np.max(b) / stats['median'] ) - ( np.min(b) / stats['median'] )

                if self.summode == self.MEAN:
                    value = stats['mean']
                elif self.summode == self.MEDIAN:
                    value = stats['median']
                elif self.summode == self.MIN:
                    value = stats['min']
                elif self.summode == self.MAX:
                    value = stats['max']
                elif self.summode == self.UPQ:
                    value = stats['upper_quartile']
                elif self.summode == self.LOQ:
                    value = stats['lower_quartile']
                elif self.summode == self.IQRSp:
                    value = stats['interquartile_range_spread']
                else:
                    value = stats['sum']
                
             

                output['raw'] = interval_data[ind]

                output['num_readings'] += 1
                output['readings'].append({ 
                    'raw': interval_data[ind],
                    'processed': True,
                    'interval_start': ind, 
                    'value': float("{0:.2f}".format(value)), 
                    'stats': stats
                }) 

        return output














def which_season(dt):
    doy    = dt.timetuple().tm_yday
    spring = range(80, 172)
    summer = range(172, 264)
    fall   = range(264, 355)
    if doy in spring:
      season_name = 'spring'
    elif doy in summer:
      season_name = 'summer'
    elif doy in fall:
      season_name = 'fall'
    else:
      season_name = 'winter'
    return season_name

def get_season_dates(year):
    previous_year = str(int(year) - 1)
    this_year     = str(year)
    return {
        'winter': {
            'start': datetime.strptime('Dec 21 '+previous_year+' 00:00:00', '%b %d %Y %H:%M:%S'),
            'end': datetime.strptime('Mar 19 '+this_year+' 23:59:59', '%b %d %Y %H:%M:%S')
        },
        'spring': {
            'start': datetime.strptime('Mar 20 '+this_year+' 00:00:00', '%b %d %Y %H:%M:%S'),
            'end': datetime.strptime('Jun 20 '+this_year+' 23:59:59', '%b %d %Y %H:%M:%S')
        },
        'summer': {
            'start': datetime.strptime('Jun 21 '+this_year+' 00:00:00', '%b %d %Y %H:%M:%S'),
            'end': datetime.strptime('Sep 22 '+this_year+' 23:59:59', '%b %d %Y %H:%M:%S')
        },
        'autumn': {
            'start': datetime.strptime('Sep 23 '+this_year+' 00:00:00', '%b %d %Y %H:%M:%S'),
            'end': datetime.strptime('Dec 20 '+this_year+' 23:59:59', '%b %d %Y %H:%M:%S')
        }
    }
   
