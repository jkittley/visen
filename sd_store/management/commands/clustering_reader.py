#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.conf import settings
from sd_store.models import *
from datetime import datetime, timedelta
from frontend.models import *
import matplotlib.pyplot as plt
from math import *
from pprint import pprint
import collections
from itertools import product, permutations
import numpy as np
import timeit
import calendar 
import json


class Command(BaseCommand):
    
    def handle(self, *args, **options):

        filename = 'shell_tools/clusters/year_2014_num_clusters_7_interval_3_hours.txt' 
        json_data=open(filename)
        data = json.load(json_data)
        json_data.close()

        print len(data)

        dates_to_cluster = {}

        cluster_count = 0
        for cluster in data:
            cluster_count += 1
            for hour_tuple in cluster:
                dates = hour_tuple[2].split('_')
                for d in dates:
                    dates_to_cluster[str(d)] = cluster_count

        pprint(dates_to_cluster) 

                
      
