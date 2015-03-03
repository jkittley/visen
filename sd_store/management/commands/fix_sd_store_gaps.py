#encoding:UTF-8
'''
Created on 8 Feb 2013

@author: ata1g11
'''
import logging
logger = logging.getLogger('custom')

from optparse import make_option
from datetime import timedelta

import numpy as np

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from sd_store.sdutils import get_meter, NoPrimaryMeterException
from sd_store.models import SensorReading, UserProfile
from django.db.transaction import commit_on_success

class Command(BaseCommand):
    help = 'detect events'
    option_list = BaseCommand.option_list + (
        make_option('--user',
                    dest='user',
                    default=None,
                    help='Select a specific user'),
        )
    
    @commit_on_success
    def handle(self, *args, **options):
        try:
            self.stdout.write("Fixing data gaps..\n")
            if options['user']:
                user = User.objects.get(username=options['user'])
                all_users = [user, ]
            else:
                all_users = User.objects.all()
            
            for user in all_users:
                try:
                    self.stdout.write("Processing user %s.. " % user)
                    meter, channel = get_meter(user)
                    
                    readings = SensorReading.objects.filter(sensor=meter, channel=channel).order_by('timestamp')
                    
                    timestamps = [x[0] for x in readings.values_list('timestamp')]
                    delta_t = np.diff(timestamps)
                    gaps = [(t, dt) for (t, dt) in zip(timestamps, delta_t) if dt > timedelta(seconds=120)]
                    
                    print 'gaps', gaps
                    for (t, dt) in gaps:
                        before, after = readings.filter(timestamp__gte=t
                                               ).filter(timestamp__lte=t+dt)
                        self.stdout.write("\n%s %.0f %s\n" % (t, 
                                                        dt.total_seconds(), 
                                                        "%.2f %.2f" % (before.value, after.value)))
    
                        gap_delta = after.timestamp - before.timestamp
                        n = int(gap_delta.total_seconds() / 120) 
                        val = after.value / n
                        
                        after.value = val
                        after.save()
                        
                        gap_timestamps = [t + i * timedelta(seconds=120) for i in range(1, n)]
                        
                        for gt in gap_timestamps:
                            new_reading = SensorReading(timestamp=gt,
                                                        value=val,
                                                        sensor=meter,
                                                        channel=channel)
                            try:
                                new_reading.save()
                            except Exception as e:
                                self.stdout.write(str(e) + "\n")
                                self.stdout.write("t: %s; meter: %s; channel: %s\n" % (t, meter, channel))
                        
                        gap_readings = readings.filter(timestamp__gte=t
                                               ).filter(timestamp__lte=t+dt)
                        self.stdout.write("\n%s %d %s\n" % (t, 
                                                        gap_readings.count(), 
                                                        str(["%.2f" % x for x in gap_readings.values_list('value')])))
                    
                    self.stdout.write(" ..done\n")
                except (NoPrimaryMeterException,UserProfile.DoesNotExist) as e:
                    self.stdout.write(str(e))
                    self.stdout.write(" ..skipping\n")
                
            self.stdout.write("The End!!..\n")

        except Exception as e:
            logger.exception('error in pull_protected_store')
            raise e

