#encoding:UTF-8
'''

@author: Ravi, Enrico 
'''

from datetime import datetime, timedelta, date
from time import mktime
from logging import getLogger
from django.db.utils import IntegrityError
logger = getLogger('custom')

from django.conf import settings
from django.db.models import Min, Max, Avg

from models import SensorReading, Baseline, Sensor
from models import UserProfile, Channel
from basicutils.general import moving_average, total_seconds
from basicutils.djutils import to_dict

# TODO: this introduces a dependency -- this is to be considered
# a temporary implementation and a cleaner solution should be found
# to make the code more properly modular

try:
    from pricing import combined
    PRICING = True
except:
    PRICING = False

#ALWAYS_ON_WINDOW_SIZE = 61 # about 2 hours
ALWAYS_ON_WINDOW_SIZE = 91 # about 3 hours

class NoPrimaryMeterException(Exception):
    """
    This is used in get_meter because None was being passed through several 
    functions before causing logic errors. This way it cannot accidentally be 
    treated as a meter, if there is none.
    """
    pass
    
def get_meter(user):
    # get primary meter, if it exists
    profile = UserProfile.objects.get(user=user)
    meter = profile.primary_sensor
    if meter == None:
        # TODO: get the meter (if there's only one)
        try:
            # TODO: replace name with type
            meter = Sensor.objects.get(user=user, sensor_type__istartswith='meter')
        except (Sensor.MultipleObjectsReturned, Sensor.DoesNotExist):
            raise NoPrimaryMeterException("No primary meter for"+repr(user))
    channel = Channel.objects.get(name='energy')
    return meter, channel

def correct_interval(existing_interval, requested_interval):
    
    if requested_interval <= existing_interval:
        return existing_interval
    else:
        return int(round(float(requested_interval) / 
                         float(existing_interval)) * existing_interval)
    
def filter_according_to_interval_gen(sensor, channel, 
                                     startTimestamp, endTimestamp, 
                                     requestedInterval, dataType):
    
    reading_list = SensorReading.objects.filter(sensor=sensor, channel=channel
                                        ).filter(timestamp__gte=startTimestamp
                                         ).filter(timestamp__lt=endTimestamp)
    if reading_list.count() == 0:
        return 
    
    dataInterval = channel.reading_frequency
    powerFactor = 60 * 60.0 / channel.reading_frequency
    
    requestedInterval = correct_interval(dataInterval, requestedInterval)
    if requestedInterval == dataInterval:
        if dataType in ('energy', 'generic'):
            for item in reading_list:
                yield item
            return
        elif dataType == 'power':
            for item in reading_list:
                item.value *= powerFactor
                yield item
            return 
        else:
            raise ValueError('dataType %s not supported' % (dataType,))
    
    requested_timedelta = timedelta(seconds=requestedInterval)
    data_timedelta = timedelta(seconds=dataInterval)
    
    value_acc = 0
    counter = 0
    first_reading = reading_list[0]
    # subtract one sampling interval because we need to consider the first data point
    prev_timestamp = first_reading.timestamp
    debug_count=0
    
    for item in reading_list:
        debug_count+=1
        
        #timestamp = 
    
        if dataType == 'power':
            value_acc += item.value * powerFactor
        else:
            value_acc += item.value
        counter += 1
        
        if item.timestamp - prev_timestamp == (requested_timedelta - data_timedelta):
            if counter == requestedInterval / dataInterval:
                if dataType in ('power', 'generic'):
                    value_acc /= counter
                
                mr = SensorReading(timestamp=prev_timestamp, 
                                   sensor=sensor, 
                                   value=value_acc)
                debug_count=0
                value_acc = 0.0
                counter = 0
                
                prev_timestamp += requested_timedelta
                
                yield mr
                
            else:
                # there is a gap higher than expected e.g. a measurement is missed
                
                # if counter == 1 this means that the previous measurement has been saved and the current one
                # has not been saved yet. 
                
                # An example where this happens is when we have sampling interval of 240 (4 minutes) and the last
                # measurement saved is 2012-01-04 12:54:00 the next measurement is 2012-01-04 13:02:00 this means that there is a gap
                # of 6 minutes
                if counter != 1:
                    # Eliminate the last measurement because it does not belong to this period
                    # essentially this is "undo"
                    if dataType == 'power':
                        value_acc -= item.value * powerFactor
                    else:
                        value_acc -= item.value
                    counter-=1
                
                if dataType in ('power', 'generic'):
                    value_acc /= counter
                
                noOfReadingsPerMR = requestedInterval/dataInterval
                
                #Check wheather we have more than half the measurements per measurement
                #If true then return the data
                #If false then skip
                if counter>=noOfReadingsPerMR/2.0:
                    mr = SensorReading(timestamp=prev_timestamp, sensor=sensor,value=value_acc)
                    yield mr
                
                debug_count = 0
                value_acc = 0
                
                #TODO This if returns true when we have 240 requested interval while it is not supposed to.
                if counter != 1:
                    #Now put the current measurement to the correct measurement period
                    if dataType == 'power':
                        value_acc += item.value * powerFactor
                    else:
                        value_acc += item.value
                    counter = 1
                else:
                    counter=0
                #for gaps bigger than the interval find the prev_timestamp that the current timestamp belongs
                currPoint =prev_timestamp 
                while currPoint <= item.timestamp:
                    currPoint += requested_timedelta
                prev_timestamp = currPoint - requested_timedelta
    
    return 

def filter_according_to_interval_sql(sensor, channel, 
                                     startTimestamp, endTimestamp, 
                                     interval, dataType):
    # the following is based on http://stackoverflow.com/questions/1607143/mysql-group-by-intervals-in-a-date-range
    #offset = - mktime( startTimestamp.timetuple() )
    if dataType == 'energy':
        query = """ \
        SELECT 
            id, 
            MIN(timestamp), 
            SUM(value) * %s AS value, 
            sensor_id 
        FROM sd_store_sensorreading WHERE
            sensor_id = %s AND
            channel_id = %s AND
            timestamp >= %s AND
            timestamp < %s 
        group by floor( (UNIX_TIMESTAMP(timestamp) - UNIX_TIMESTAMP(%s)) / %s )
        """
        powerFactor = 1.0
    elif dataType == 'power':
        query = """ \
        SELECT
            id, 
            MIN(timestamp), 
            AVG(value) * %s AS value, 
            sensor_id 
        FROM sd_store_sensorreading WHERE
            sensor_id = %s AND
            channel_id = %s AND
            timestamp >= %s AND
            timestamp < %s 
        group by floor( (UNIX_TIMESTAMP(timestamp) - UNIX_TIMESTAMP(%s)) / %s )
        """
        powerFactor = 60 * 60.0 / channel.reading_frequency
    elif dataType == 'generic':
        query = """ \
        SELECT
            id, 
            MIN(timestamp), 
            AVG(value) * %s AS value, 
            sensor_id 
        FROM sd_store_sensorreading WHERE
            sensor_id = %s AND
            channel_id = %s AND
            timestamp >= %s AND
            timestamp < %s 
        group by floor( (UNIX_TIMESTAMP(timestamp) - UNIX_TIMESTAMP(%s)) / %s )
        """
        powerFactor = 1.0
    else:
        raise ValueError('dataType %s not supported' % (dataType,))

    params = (powerFactor, sensor.pk, channel.pk, 
              startTimestamp, endTimestamp, startTimestamp, interval)

    return SensorReading.objects.raw( query, params )

def filter_according_to_interval_sqlite(sensor, channel, 
                                     startTimestamp, endTimestamp, 
                                     interval, dataType):
    # the following is based on http://stackoverflow.com/questions/1607143/mysql-group-by-intervals-in-a-date-range
    # with workarounds for sqllite based on:
    # http://stackoverflow.com/questions/3693076/unix-timestamp-in-sqlite
    # and http://stackoverflow.com/questions/7129249/getting-the-floor-value-of-a-number-in-sqlite
    if dataType == 'energy':
        query = """ \
        SELECT 
            id, 
            MIN(strftime('%%s', timestamp)), 
            SUM(value) * %s as 'value', 
            sensor_id 
        FROM sd_store_sensorreading WHERE
            sensor_id = %s AND
            channel_id = %s AND
            timestamp >= %s AND
            timestamp < %s 
        group by cast( (SELECT strftime('%%s', timestamp) - strftime('%%s', %s)) / %s as int)
        """
        powerFactor = 1.0
    elif dataType == 'power':
        query = """ \
        SELECT
            id, 
            MIN(cast(timestamp as int)),
            AVG(value) * %s AS value, 
            sensor_id 
        FROM sd_store_sensorreading WHERE
            sensor_id = %s AND
            channel_id = %s AND
            timestamp >= %s AND
            timestamp < %s 
        group by cast( (SELECT strftime('%%s', timestamp) - strftime('%%s', %s)) / %s as int)
        """
        powerFactor = 60 * 60.0 / channel.reading_frequency
    elif dataType == 'generic':
        query = """ \
        SELECT
            id, 
            MIN(cast(timestamp as int)),
            AVG(value) * %s AS value, 
            sensor_id 
        FROM sd_store_sensorreading WHERE
            sensor_id = %s AND
            channel_id = %s AND
            timestamp >= %s AND
            timestamp < %s 
        group by cast( (SELECT strftime('%%s', timestamp) - strftime('%%s', %s)) / %s as int)
        """
        powerFactor = 1.0
    else:
        raise ValueError('dataType %s not supported' % (dataType,))
    
    # round the startTimestamp to match the interval
    #print 'startTimestamp:', startTimestamp
    #import time
    #startTimestamp = datetime.fromtimestamp(int(time.mktime(startTimestamp.timetuple()) / interval) * interval) 
    #print 'offset:', offset
    #print 'interval:', interval
    
    params = (powerFactor, sensor.pk, channel.pk, 
              startTimestamp, endTimestamp, startTimestamp, interval)
    
    return SensorReading.objects.raw( query, params ) 


def filter_according_to_interval(*args):
    if settings.HOSTING in ('deployment', 'localdeployment'):
        return filter_according_to_interval_sql(*args)
    else:
        #return filter_according_to_interval_gen(*args)
        return filter_according_to_interval_sqlite(*args)


# TODO: move this to models.Meter ?
def calculate_always_on(sensor, channel, start, end, 
                        requested_interval, data_type):
    power_factor = 60 * 60.0 / channel.reading_frequency
    baseline_dataset = []
    
    if requested_interval <= 0:
        requested_interval = channel.reading_frequency
    
    # get the 
    start_day = start.date()
    end_day = end.date()
    no_days = (end_day - start_day).days
    #no_days = max(no_days, 1)
    no_days += 1
    
    logger.debug('calculate_always_on -- start: ' + str(start))
    logger.debug('calculate_always_on --   end: ' + str(end))
    logger.debug('calculate_always_on -- no_days: %d' % (no_days))
    
    for day in [start_day + timedelta(days=i) for i in range(no_days)]:
        day = datetime(day.year, day.month, day.day)
        curr_start = max(day, start)
        curr_end = min(day + timedelta(hours=24), end)
        dayBaseline = getDayBaseline(sensor, channel, day, data_type)
        if data_type == 'power':
            dayBaseline *= power_factor
        else:
            scale_factor = requested_interval / channel.reading_frequency 
            dayBaseline *= scale_factor
        
        no_points = int(total_seconds(curr_end - curr_start) / 
                        requested_interval)
        day_range = [curr_start + j * timedelta(seconds=requested_interval
                                                ) for j in range(no_points)]
        for t in day_range:
            baseline_dataset.append([t,dayBaseline])
    
    return baseline_dataset

# TODO: this method needs cleaning
def calculate_event(event):
    # This function populates a json object representing the event
    # the event data is not sent to the client, as the client gets the data 
    # from the main data plot. Only aggregate information is used here.
    
    logger.debug('calculate_event:', event.id)
    
    event_dict = to_dict(event)
    
    always_on = calculate_always_on(event.sensor, 
                                    event.channel,
                                    event.start, 
                                    event.end + timedelta(minutes=2), 
                                    event.channel.reading_frequency,
                                    'energy')
    
    total_event_baseline = sum([x[1] for x in always_on])
    
    event_dict['total_always_on'] = total_event_baseline
    # calculate consumption, without always on
    event_dict['net_consumption'] = event_dict['total_consumption'] - total_event_baseline
    
    # break down consumption into days
    # get readings
    readings = SensorReading.objects.filter(sensor=event.sensor,
                                            channel=event.channel,
                                            timestamp__gte=event.start,
                                            timestamp__lt=event.end)
    
    days = (event.end.date() - event.start.date()).days
    #print 'days', event.end.date() - event.start.date()
    #print event.duration
    #print
    daily_energy = {}
    if days > 1:
        for d in range(days+1):
            curr_start = event.start.date() + timedelta(days=d)
            curr_end = event.start.date() + timedelta(days=d+1)
            selected = readings.filter(timestamp__gte=curr_start,
                                       timestamp__lt=curr_end)
            
            power_factor = 60 * 60.0 / event.channel.reading_frequency
            mean_power = power_factor * selected.aggregate(Avg('value'))['value__avg']
            actual_start = selected.aggregate(Min('timestamp'))['timestamp__min']
            actual_end = selected.aggregate(Max('timestamp'))['timestamp__max']
            duration = (actual_end - actual_start).total_seconds() / 60.0 / 60.0
            
            #TODO: split the always-on
            ts = int(mktime(curr_start.timetuple()) * 1000)
            daily_energy[ts] = mean_power * duration
            #print 'daily_energy', curr_start, daily_energy[ts]
        
    event_dict['per_day'] = daily_energy
    
    if PRICING:
        prices = combined.get_actual_prices(event.start, event.end, 0.5, 0.5)
        # TODO make this more precise
        avg_price = sum(prices) / float(len(prices))
        
        event_dict['cost'] = event_dict['net_consumption'] * avg_price
            
    return event_dict

# get the baseline value for the specific period (a day)
def getDayBaseline(meter, channel, day, data_type):
    day = day.date()
    try:
        baseline = Baseline.objects.get(date=day, 
                                        sensor=meter,
                                        channel=channel)
        created = False
    except Baseline.DoesNotExist:
        baseline = Baseline(date=day, 
                            sensor=meter,
                            channel=channel,
                            value=0.0)
        created = True
    
    logger.debug('getDayBaseline')
    #powerFactor = 60 * 60.0 / channel.reading_frequency
    
    valid = False
    if not created:
        lastModifiedDay = baseline.last_modified.date()
        if day == date.today():
            if (datetime.now() - baseline.last_modified) < timedelta(hours=1):
                # TODO: check me!
                valid = True
        else: # day is not today
            if lastModifiedDay > day: 
                valid = True
    
    logger.debug('valid: ' + str(valid))
    
    if valid:
        return baseline.value
    else:
        # filter all energy data from the specific reading meter and specific period (1 day)
        filter_energy_objects = SensorReading.objects.filter(
                             sensor=meter, channel=channel).filter(
                             timestamp__gte=day).filter(
                             timestamp__lt=(day+timedelta(days=1)) )

        logger.debug('filter_energy_objects.count(): ' + 
                     str(filter_energy_objects.count()))
        
        if filter_energy_objects.count() > 0:
            energy = [x.value for x in filter_energy_objects]
            
            # hard-coded subset size for moving average calculation
            window_size = ALWAYS_ON_WINDOW_SIZE
            
            mav = moving_average(energy, window_size)
            import numpy as np
            # calculate the moving average using a rectangular window
            window = (np.zeros(int(window_size)) + 1.0) / window_size
            mav = np.convolve(energy, window, 'valid')

            try:
                min_baseline = min( mav )
            except ValueError:
                min_baseline = 0 
        else:
            min_baseline = 0
        
        baseline.value = min_baseline
        try:
            baseline.save()
        except IntegrityError:
            b2 = Baseline.objects.get(date=day, 
                                            sensor=meter,
                                            channel=channel)
            b2.value = min_baseline
            b2.save()
        
        return min_baseline
    
# this function is a failed attempt to perform the calculation in SQL
# left here for reference
def getDayBaseline_sql(meter, channel, day):
    logger.debug('getDayBaseline_sql')
    startTimestamp = datetime.utcfromtimestamp(int(day))
    endTimestamp = datetime.utcfromtimestamp(int(day+timedelta(day=1)))            
    
    # hard-coded subset size for moving average calculation
    windowSize = 10 

    # the following is based on http://forums.mysql.com/read.php?10,37502,37715#msg-37715
    query = """ 
    SELECT 
        t1.id as id,  
        t1.sensor_id as sensor_id,  
        t1.channel_id as channel_id,  
        t1.timestamp as timestamp, 
        AVG(t2.value) as value 
    FROM 
        sd_store_meterreading AS t1 
    LEFT JOIN 
        sd_store_meterreading AS t2
    ON
        t2.timestamp BETWEEN DATE_SUB(t1.timestamp, INTERVAL %s SECOND) AND t1.timestamp 
    WHERE 
        t1.sensor_id = %s AND 
        t1.channel_id = %s AND 
        t1.timestamp > %s AND 
        t1.timestamp <= %s AND 
        t1.value > 0 
    """
    
    interval = windowSize * meter.reading_frequency
    params = (interval, meter.pk, channel.pk, startTimestamp, endTimestamp)
    logger.debug( 'params: ' + str(params) )
    # filter all energy data from the specific reading meter and specific period (1 day)
    filter_energy_objects = SensorReading.objects.raw( query, params )
    
    filter_energy_objects = [x.value for x in filter_energy_objects]
    logger.debug( "result: " + str( filter_energy_objects[:5] ) )
    
    try:
        min_baseline = min( filter_energy_objects )
    except ValueError:
        min_baseline = 0
    
    return min_baseline

def get_washing_machine_plug(user):
    try:
        return Sensor.objects.get(user=user, sensor_type='SmartPlug')
    except Sensor.MultipleObjectsReturned:
        # look at the descriptions to find the right one
        return Sensor.objects.get(user=user, sensor_type='SmartPlug', name__icontains='washing machine')
    except Sensor.DoesNotExist:
        return None


