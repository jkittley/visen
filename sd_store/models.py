#encoding:UTF-8
from django.db import models
from django.db.models import Max, Min, Avg, StdDev

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
#from django.utils import simplejson as json
#from django.core.files.storage import FileSystemStorage

from basicutils.djutils import LOCALE_DATE_FMT
from django.db.utils import DatabaseError

from decimal import Decimal

#fs = FileSystemStorage()

class ChannelManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

class Channel(models.Model):
    objects = ChannelManager()
    
    name = models.CharField(max_length=32)
    unit = models.CharField(_('unit of measurement'), max_length=10)
    reading_frequency = models.IntegerField(_('reading frequency in seconds'))
    def natural_key(self):
        return self.name
    
    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.reading_frequency)
    class Meta:
        unique_together = ('name', 'reading_frequency',)

class SensorManager(models.Manager):
    def get_by_natural_key(self, mac):
        return self.get(mac=mac)
    
# should Sensor be abstract? Not clear how Django deals with abstract
# inheritance and keys ..can I iterate over all instances inheriting from abstract?
class Sensor(models.Model):
    objects = SensorManager()
    
    mac = models.CharField(_('ID number'), max_length=30, unique=True, db_index=True)
    sensor_type = models.CharField(_('sensor type'), max_length=30)
    name = models.CharField(_('metering source'), max_length=30)
    user = models.ForeignKey(User)
    channels = models.ManyToManyField(Channel)
    
    hidden_fields = ('sensor_ptr',)
    
    def __unicode__(self):
        return u'%s [%s]' % (self.name, self.mac)
    
    def natural_key(self):
        return self.mac

class Meter(Sensor):
    pass

class SmartPlug(Meter):
    pass

class Button(Sensor):
    pass
    
class SensorReading(models.Model):
    timestamp = models.DateTimeField(db_index=True)
    sensor = models.ForeignKey(Sensor, db_index=True)
    channel = models.ForeignKey(Channel, db_index=True)
    value = models.FloatField(_('value'),default=0)

    class Meta:
        ordering = ['timestamp']
        unique_together = (('timestamp', 'sensor', 'channel'),)

    def __unicode__(self):
        return str(self.value) + ' @ ' + self.timestamp.strftime(LOCALE_DATE_FMT)
    
    hidden_fields = ['sensor', 'channel', 'id']

class RawDataKey(models.Model):
    value = models.CharField(max_length=32)
    sensors = models.ManyToManyField(Sensor)

# this is the always-on energy
# rename to SensorBaseline ?
class Baseline(models.Model):
    date = models.DateField(db_index=True)
    sensor = models.ForeignKey(Sensor, db_index=True)
    channel = models.ForeignKey(Channel, db_index=True)
    value = models.FloatField()
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('date', 'sensor', 'channel'),)


class MeteringPoint(models.Model):
    name = models.CharField(_('unique name'), max_length=30, unique=True)
    description = models.CharField(_('description'), max_length=30, blank=True)
    sensor = models.ForeignKey(Sensor, null=True)
    user = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.name
    
#    def to_json(self):
#        hidden_fields = ['id']
#        
#        meta_field_dict = {}
#        for field in self._meta.fields:
#            if hidden_fields.count(field.name) != 0:
#                pass
#            elif field.name == 'user' or field.name == 'sensor':
#                meta_field_dict[field.name] = str(getattr(self, field.name))
#            else:
#                meta_field_dict[field.name] = getattr(self, field.name)
#        return json.dumps(meta_field_dict)

class EventTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

class EventType(models.Model):
    objects = EventTypeManager()
    
    name = models.CharField(_('icon name'), max_length=30, unique=True)

    icon = models.URLField()
    alt_icon = models.URLField()
    
    def natural_key(self):
        return self.name
    
    def __unicode__(self):
        return self.name
    
# Added by dpr1g09 -- to hold details of the predictions
class EventTypePrediction(models.Model):
    event_type = models.ForeignKey(EventType)
    certainty = models.FloatField()
    user_accepted = models.BooleanField(default=False)    
    
class Event(models.Model):
    
    # null=True because auto_detected won't initially have a type -- dpr1g09
    # TODO: change this, I am sure there is a better alternative,
    # e.g. set the type to undefined
    event_type = models.ForeignKey(EventType, null=True) 
    name = models.CharField(_('unique name'), max_length=1024)
    description = models.CharField(_('description'), max_length=1024, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    #user = models.ForeignKey(User)
    sensor = models.ForeignKey(Sensor)
    channel = models.ForeignKey(Channel)
    
    auto_detected = models.BooleanField(default=False, blank=True)
    
    @property
    def duration(self): 
        return (self.end - self.start).total_seconds() / 60.0

    def get_readings_list(self):
        return SensorReading.objects.filter(sensor=self.sensor, 
                                                    channel=self.channel,
                                                    timestamp__gte=(self.start),
                                                    timestamp__lt=(self.end))
    
    _maximum_power = models.FloatField(null=True, blank=True)
    @property
    def maximum_power(self):
        if self._maximum_power is None:
            #power_factor = 60 * 60.0 / self.channel.reading_frequency
            power_factor = 1.0
            self._maximum_power = power_factor * self.get_readings_list().aggregate(Max('value'))['value__max']
            self.save()
        return self._maximum_power
    
    _minimum_power = models.FloatField(null=True, blank=True)
    @property
    def minimum_power(self):
        if self._minimum_power is None:
            power_factor = 60 * 60.0 / self.channel.reading_frequency
            self._minimum_power = power_factor * self.get_readings_list().aggregate(Min('value'))['value__min']
            self.save()
        return self._minimum_power

    _mean_power = models.FloatField(null=True, blank=True)
    @property
    def mean_power(self):
        if self._mean_power is None:
            power_factor = 60 * 60.0 / self.channel.reading_frequency
            self._mean_power = power_factor * self.get_readings_list().aggregate(Avg('value'))['value__avg']
            self.save()
        return self._mean_power

    def __calculate_sqllite_stdev(self):
        # TODO: check the following!
        # from http://stackoverflow.com/questions/2298339/standard-deviation-for-sqlite
        # SELECT AVG((t.row-sub.a)*(t.row-sub.a)) as var from t, (SELECT AVG(row) AS a FROM t) AS sub;
#        query = """ \
#        SELECT
#            AVG((value - sub.a)*(value - sub.a)) AS value__stddev 
#        FROM sd_store_sensorreading, (SELECT AVG(value) AS a FROM sd_store_sensorreading) AS sub 
#        WHERE
#            sensor_id = %s AND
#            channel_id = %s AND
#            timestamp > %s AND
#            timestamp <= %s, 
#        
#        """
#        params = (self.sensor.pk, self.channel.pk,
#                    self.start, self.end)
#        return SensorReading.objects.raw( query, params )['value__stddev']
        readings = self.get_readings_list()
        import numpy as np
        return np.std([x.value for x in readings])

    _standard_deviation = models.FloatField(null=True, blank=True)
    @property
    def standard_deviation(self):
        if self._standard_deviation is None:
            try:
                self._standard_deviation = self.get_readings_list().aggregate(StdDev('value'))['value__stddev']
            except DatabaseError:
                self._standard_deviation = self.__calculate_sqllite_stdev()
            self.save()
        return self._standard_deviation
    
    @property
    def total_consumption(self): 
        #return self.mean_power * self.duration * 60.0 / self.channel.reading_frequency
        return self.mean_power * self.duration / 60.0 
    
    @property
    def hour_of_day(self): return self.start.hour
    
    @property
    def day_of_week(self): return self.start.weekday()
    
    extra_fields = ('maximum_power', 'minimum_power', 'mean_power', 
                    'standard_deviation', 'total_consumption',
                    'hour_of_day', 'day_of_week')
    
    # the following field is for automatic detection
    # null=True should make it retro-compatible
    predictions = models.ManyToManyField(EventTypePrediction, null=True, blank=True)
    
    metering_points = models.ManyToManyField(MeteringPoint, blank=True)
    
    def __unicode__(self):
        return self.name

    
class Goal(models.Model):
    name = models.CharField(_('name'), max_length=30)
    description = models.CharField(_('description'), max_length=30, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    user = models.ForeignKey(User)
    consumption = models.FloatField(_('total consumption during event'))
    
    def __unicode__(self):
        return self.name
    
    
class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    
    primary_sensor = models.ForeignKey('Sensor', blank=True, null=True)
    phone_number = models.CharField(max_length=32, blank = True, null = True)
    sms_reminder = models.BooleanField(default = True)
    email_reminder = models.BooleanField()
    sms_alert = models.BooleanField(default = True)
    email_alert = models.BooleanField()
    price_increase = models.DecimalField(max_digits=4, decimal_places=2, default = Decimal('0.5'))
    #fe_allowed_users = models.ManyToManyField('self', blank=True, null=True)
    
    def baseline_consumption(self):
        return StudyInfo.objects.get(user=self).baseline_consumption
    
    def start_date(self):
        return StudyInfo.objects.get(user=self).start_date
    
    def __unicode__(self):
        return u"%s" % (self.user,)

class StudyInfo(models.Model):
    user = models.ForeignKey(User, db_index=True, unique=True)
    baseline_consumption = models.FloatField()
    start_date = models.DateTimeField()
    last_modified = models.DateTimeField(auto_now=True)
    initial_credit = models.FloatField()
    
# TODO: is this ever used?
#class Billing(models.Model):     
#    user = models.ForeignKey(User)     
#    timestamp = models.DateTimeField()     
#    amount_used = models.FloatField(blank=False, null=False)     
#
## TODO: move the following three models to a battery django-app?
#class Booking(models.Model):
#    # fixed parameters
#    user = models.ForeignKey(User)     
#    name = models.CharField(max_length=30)
#    duration = models.FloatField()
#    # This is the TOTAL load over the duration of the booking     
#    load = models.FloatField()
#    
#    # parameters that depend on pricing / optimisation
#    start = models.DateTimeField()
#    price = models.FloatField()
#    
#    original_start = models.DateTimeField(blank=True)
#    original_price = models.FloatField(blank=True)
#    
#    created = models.DateTimeField(_('booking made at'), auto_now_add=True)
#    
#    
#    def save(self, *args, **kwargs):
#        if self.original_start is None:
#            self.original_start = self.start
#        if self.original_price is None:
#            self.original_price = self.price
#        super(Booking, self).save(*args, **kwargs)
#
#class BatteryType(models.Model):
#    capacity = models.FloatField()
#    charging_rate = models.FloatField()
#    leakage_rate = models.FloatField()
#    efficiency = models.FloatField() 
#    max_discharge_rate = models.FloatField()
#    
#class BatteryStatus(models.Model):
#    class Meta:
#        unique_together = (('user', 'timestamp'),)
#    
#    user = models.ForeignKey(User)
#    battery_type = models.ForeignKey(BatteryType)
#    timestamp = models.DateTimeField(db_index=True)
#    charge_rate = models.FloatField(blank=False, null=False)
#    charge_level = models.FloatField(blank=True, null=True) 
#    charge_cost = models.FloatField(blank=True, null=True) 
#    # consumption rate is charge_rate + consumption sensed 
#    # from the plug in the same time interval e.g. if the appliance is
#    # used "out of plan"
#    consumption = models.FloatField(blank=False, null=False)
#    consumption_cost = models.FloatField(blank=False, null=False)
     
# Not sure if this is necessary, or would scale easily. -- dpr1g09        
class DetectionLog(models.Model):
    sensor = models.ForeignKey(Sensor)
    timestamp = models.DateTimeField(auto_now = True)
    comment = models.CharField(max_length = 256)


#CONSTRAINT_TYPES = (
#                     (0, 'booking'),
#                     (1, 'notification')
#                     )
#
##DAY_OF_WEEK = ()
#
#class UnavailableInterval(models.Model):
#    start = models.TimeField()
#    end = models.TimeField()
#    weekday = models.IntegerField()
#    user = models.ForeignKey(User)
#    constraint_type = models.CharField(max_length=1, choices=CONSTRAINT_TYPES)
#    



