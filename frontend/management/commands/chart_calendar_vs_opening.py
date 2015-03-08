#encoding:UTF-8
# 
# Produce a Radar diagram for each site.
# Each radar shows the opening hours, gas and electric for the period specified
# 
# 

import os
import datetime, math, json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.spines import Spine
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
from frontend.models import *
from dateutil.rrule import rrule, DAILY, MINUTELY
from matplotlib.dates import WeekdayLocator
from sklearn.preprocessing import normalize

class Command(BaseCommand):
    help = 'Produce a Radar diagram for each sensors gas and electricity channels, then overlayed with opening hours'
    option_list = BaseCommand.option_list + (
            make_option('--period',
                    dest='period_str',
                    default=None,
                    help='A time period to display e.g. yyyy-mm-dd,yyyy-mm-dd'),
            make_option('--filter',
                    dest='filter',
                    default=None,
                    help='A string which is used to filter the sensors processed'),
            make_option('--file',
                    dest='filename',
                    default=None,
                    help='A filename where to save the plot'),
            make_option('--normalize',
                    action="store_true",
                    dest='normalize',
                    default=False,
                    help='Normalize the sensor readings (No value required)'),
            make_option('--open_or_not',
                    action="store_true",
                    dest='open_or_not',
                    default=False,
                    help='If used opening times will be reduced to open or closed instead of number of hours'),
    )


    def handle(self, *args, **options):

        # Process periods
        sample_period = []
        try:
            subset = options['period_str'].split(',')
            start = datetime.strptime(subset[0].strip(),'%Y-%m-%d')
            end   = datetime.strptime(subset[1].strip(),'%Y-%m-%d')
        except:
            print "Date invalid Format:", options['period_str'], "Format should be yyyy-mm-dd,yyyy-mm-dd"
            return

        # Check if they entered any dates or periods
        if start > end:
            print "The period must no end before it starts"
            return

        
    

                
                
