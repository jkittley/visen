#encoding:UTF-8
import time, json, math, calendar, sys
from datetime import datetime, date, timedelta

from sd_store.models import *
from frontend.models import *
from frontend.forms import *
from django.db.models import Sum, Q

from itertools import tee, izip

from operator import add
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from sklearn.cluster import MeanShift, estimate_bandwidth
from math import *
from itertools import product, permutations
from operator import itemgetter

from scipy.stats import linregress
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, to_tree

# ----------------------------------------------------------------------------- 
# CHART - Controller
# -----------------------------------------------------------------------------

def build_data(vis):
    if vis.chart.ref == 'calendar':
        return build_data_cal(vis)
    if vis.chart.ref == 'time':
        return build_data_time(vis)
    if vis.chart.ref == 'scatter':
        return build_data_scatter(vis)
    if vis.chart.ref == 'table':
        return build_data_table(vis)
    if vis.chart.ref == 'calcluster':
        return build_data_cal_cluster(vis)
    if vis.chart.ref == 'star':
        return build_data_star(vis)
    if vis.chart.ref == 'box':
        return build_data_box(vis)
    if vis.chart.ref == 'histogram':
        return build_data_histogram(vis)
    return { 'messages': ['Failed to locate build function'], 'series':[] }



def build_data_histogram(vis):
    
    master = []
    
    # Fetch inputs
    inputs = vis.get_all_inputs()

    # Check all inputs have the same time periods
    for visin in inputs:

        data = {}
        data['vis_settings'] = vis.get_settings()
        data['messages'] = []
        data['series']   = []
        data['xAxis'] = { 
            'title': { 
                'text': 'Bins',
                'style': {
                    'fontSize': '8px'
                }
            }, 
            'categories': [], 
            'labels': { 
                'enabled':1, 
                'rotation': -90,
                'style': {
                    'fontSize': '8px'
                }
            } 
        }
        data['yAxis'] = {
            'title': { 
                'text': 'Frequency',
                'style': {
                    'fontSize': '8px'
                } 
            }, 
            'labels': { 
                'enabled':1,
                'rotation': -90,
                'style': {
                    'fontSize': '8px'
                }
            }
        }

        # Build channel name
        namestr = ''
        if visin.name != '':
            namestr = visin.name,
        else:
            namestr = visin.sensor.name + ' ' +visin.channel.name

        data['title'] = namestr

        # Process the readings
        input_data = visin.get_readings()
        for r in input_data['readings']:
            histogram, binedges = r['stats']['histogram']

            for edge in binedges:
                if edge >= 1:
                    data['xAxis']['categories'].append( round(float(edge),2) );

            data['series'].append({ 
                    'name': namestr,
                    'data': histogram.tolist(),
                    'tooltip': {
                        'headerFormat': '<em>Bin Edge: {point.key}</em><br/>',
                        'pointFormat': '<em>Freq: {point.y}</em><br/>',
                    }
            })

        master.append(data)

    return master



# ------------------------------------------------------------------------------------
# CHART - Box Plot
# ------------------------------------------------------------------------------------

def build_data_box(vis):

    data = {}
    data['vis_settings'] = vis.get_settings()

    data['messages'] = []
    data['series']   = []
    data['xAxis'] = {
        'categories': [],
    }

    data['yAxis'] = {
        'title': {
            'text': 'Readings'
        }
    }
    
    # Fetch inputs
    inputs = vis.get_all_inputs()

    # Check all inputs have the same time periods
    intervals = []
    for visin in inputs:
        if visin.interval not in intervals:
            intervals.append(visin.interval)
    if len(intervals) != 1:
        data['messages'].append('Intervals do not match');
        return data

    # Process all inputs
    for visin in inputs:
        
        tmp_data = []

        # Build channel name
        namestr = ''
        if visin.name != '':
            namestr = visin.name,
        else:
            namestr = visin.sensor.name + ' ' +visin.channel.name

        # Process the readings
        input_data = visin.get_readings()

        if not input_data:
            break

        for r in input_data['readings']:
            tmp_data.append([ r['stats']['min'] , r['stats']['lower_quartile'] , r['stats']['median'] , r['stats']['upper_quartile'] , r['stats']['max'] ])

            catname = visin.get_interval_mode(r['interval_start'])[1]
            if catname not in data['xAxis']['categories']:
                data['xAxis']['categories'].append( catname );

        if len(tmp_data) > 0:
            data['series'].append({ 
                'name': namestr,
                'data': tmp_data,
                'tooltip': {
                    'headerFormat': '<em>{point.key}</em><br/>'
                }
            })
        else:
            data['messages'].append('[ NO DATA ] '+visin.sensor.name + ' ' +visin.channel.name)


        #  {
        #     name: 'Outlier',
        #     color: Highcharts.getOptions().colors[0],
        #     type: 'scatter',
        #     data: [ // x, y positions where 0 is the first category
        #         [0, 644],
        #         [4, 718],
        #         [4, 951],
        #         [4, 969]
        #     ],
        #     marker: {
        #         fillColor: 'white',
        #         lineWidth: 1,
        #         lineColor: Highcharts.getOptions().colors[0]
        #     },
        #     tooltip: {
        #         pointFormat: 'Observation: {point.y}'
        #     }
        # }]
    
    

    # # Return the data
    return data
 




# ------------------------------------------------------------------------------------
# CHART - Star Plot
# ------------------------------------------------------------------------------------

def build_data_star(vis):

    data = { 'sets':[], 'messages':[], 'line':[], 'linecats':[] }
    data['vis_settings'] = vis.get_settings()

    # For each sensor add channel data
    for visin in vis.get_all_inputs():
        
        input_data = visin.get_readings()
        tmp_output = {}

        if input_data == None:
            return None

        for r in input_data['readings']: 
            imname, imstr = visin.get_interval_mode(r['interval_start'])
            ts = imstr
            if math.isnan(r['value']):
                r['value'] = 0; 
            tmp_output[ts]  = r['value'] 

        tmp_line = []
        tmp_set  = {
            'tooltip': visin.sensor.name+': '+visin.channel.name,
            'className': 'visin_'+str(visin.pk),
            'axes': []         
        }

        for ts in tmp_output:
            tmp_set['axes'].append({'axis': ts, 'value': tmp_output[ts] })
            tmp_line.append([ts, (tmp_output[ts]/np.max(np.array(tmp_output.values()))) ]) 
    
        # Sort results (Highcharts needs them in order!)
        tmp_set['axes'].sort(key=lambda x: x['axis'], reverse=True)
        tmp_line.sort(key=lambda x: x[0])
        
        # Move the last to the front
        if len(tmp_set['axes']) > 1:
            tmp_set['axes'].insert(0, tmp_set['axes'].pop(len(tmp_set['axes'])-1))
            
        # Add to master output if there are values 
        if len(tmp_set['axes']) > 0:
            data['sets'].append([ tmp_set ])
            data['line'].append({ 
                'name': tmp_set['tooltip'],
                'data': tmp_line 
            })
        else:
            data['messages'].append('[ NO DATA ] ' + tmp_set['tooltip']);


    return data 






# ----------------------------------------------------------------------------- 
# CHART - Table
# -----------------------------------------------------------------------------

def build_data_table(vis):
    data = { 
        'columns':[
            { "title": "Sensor" },
        ],
        'dataSet': []
    }
    data['vis_settings'] = vis.get_settings()

    unique_sensors  = []
    unique_channels = []
    
    # Get the oldest year and the newest
    start, end = vis.get_input_tme_span()
    earliest_date    = start.year
    most_recent_date = end.year
    if not earliest_date or not most_recent_date:
        return None

    # For each sensor add channel data
    for visin in vis.get_all_inputs():

        # Build unique list of sensors
        if visin.sensor not in unique_sensors:
            unique_sensors.append(visin.sensor)

        # Build unique list of channels
        if visin.channel not in unique_channels:
            unique_channels.append(visin.channel)
    
    # Add a column for each channel 
    for ch in unique_channels:
        data['columns'].append( { "title": ch.name+' '+visin.channel.unit })
    
    
    # Now calculate data for each channel of each sensor
    for sen in unique_sensors:

        profile = Sensor_profile.objects.all().get(sensor=sen)
        tmpdata = [profile.longname]

        for ch in unique_channels:
            tmptotal = SensorReading.objects.all().filter(sensor=sen, channel=ch, timestamp__range=(start, end)).aggregate(summed=Sum('value'))
            if tmptotal['summed']:
                tmpdata.append(int(tmptotal['summed']))
            else:
                tmpdata.append('-')

        data['dataSet'].append(tmpdata)

    return data












# ----------------------------------------------------------------------------- 
# CHART - Calendar
# -----------------------------------------------------------------------------

def build_data_cal(vis):
    
    data = { 'sets':[], 'messages':[] }
    data['vis_settings'] = vis.get_settings()

    global_highest   = 0
    global_lowest    = None
    global_unit      = None

    # Get the oldest year and the newest
    start, end = vis.get_input_tme_span()
    earliest_date    = start.year
    most_recent_date = end.year
    if not earliest_date or not most_recent_date:
        return None

    # For each sensor add channel data
    for visin in vis.get_all_inputs():

        tmpdata       = {}
        daytotal      = {}
        val_gt_zero   = False
        local_highest   = 0
        local_lowest    = None

        # Load and process the readings
        input_data = visin.get_readings()
        for r in input_data['readings']: 
            ts = r['interval_start'].strftime('%Y-%m-%d')
            daytotal[ts] = r['value']

            if r['value'] > 0:
                val_gt_zero = True

            if (r['value'] > global_highest):
                global_highest = r['value']

            if (global_lowest==None or r['value'] < global_lowest):
                global_lowest = r['value']
            
            if (r['value'] > local_highest):
                local_highest = r['value']

            if (local_lowest==None or r['value'] < local_lowest):
                local_lowest = r['value']

            if global_unit == None:
                global_unit = visin.channel.unit
                        
        tmpdata['showname']            = str(visin.channel.name)+': '+str(visin.sensor.name)
        tmpdata['showunit']            = visin.channel.unit
        tmpdata['daytotals']           = daytotal
        tmpdata['local_highest']       = local_highest
        tmpdata['local_lowest']        = local_lowest

        if val_gt_zero:
            data['sets'].append(tmpdata);
        else:
            data['messages'].append('[ NO DATA ] ' + tmpdata['showname']);

    data['global_unit']       = global_unit
    data['highest']           = global_highest
    data['lowest']            = global_lowest
    data['year']              = 2014
    data['earliest_year']     = int(earliest_date)
    data['most_recent_year']  = int(most_recent_date)
    return data











# ----------------------------------------------------------------------------- 
# CHART - Calendar Cluster
# -----------------------------------------------------------------------------

def build_data_cal_cluster(vis):
    
    data = { 'sets':[], 'messages':[], 'patterns': { 'cats':[], 'data':[] } }
    data['vis_settings'] = vis.get_settings()

    # Get the oldest year and the newest
    start, end = vis.get_input_tme_span()
    
    # Get the first (there should only be 1) input
    visin = None
    for v in vis.get_all_inputs():
        visin = v
        break

    if not visin:
        return None
    else:

        # Settings
        interval_hours    = int ( data['vis_settings']['interval_hours'] )
        year              = visin.period_start.year 
        clusters_requires = int (data['vis_settings']['clusters_requires'] )
        initdate          = datetime.strptime('Jan 01 '+str(year), '%b %d %Y')
        aday              = timedelta(days=1)        
        processing_list   = [] 
        pro_list_lookup   = []     
        interval_totals   = {}

        # Add cats
        for i in range(0, 24/interval_hours):
            data['patterns']['cats'].append(str(i*interval_hours)+':00')

        # Load readings
        print >>sys.stderr, '>>>> Loading Readings'
        readings = SensorReading.objects.filter(sensor=visin.sensor, channel=visin.channel, timestamp__range=(start, end))
        
        # Number of days to process after the start date
        delta   = end - start
        numdays = delta.days
        print >>sys.stderr, '>>>> Number of days in period ', numdays

        # Make an empty slot for each interval - stops numpy issue
        aday = timedelta(days=1)
        for dc in range(0,numdays+1):
            tmp_day = start + (aday * dc)
            day_ref = tmp_day.strftime('%Y-%m-%d')
            
            interval_totals[day_ref] = {}
            for i in range(0, 24/interval_hours):
                interval_totals[day_ref][i] = -1

        print >>sys.stderr, '>>>> Processing reading'

        # Loop through each day from start date
        for r in readings:

            # Get the sensor readings for that day and build a refrence for the day
            day_ref      = r.timestamp.strftime('%Y-%m-%d')

            # Put readings into interval segments
            if r.timestamp.hour > 0:
                key   = ceil(r.timestamp.hour / interval_hours)
            else:
                key = 1
            interval_totals[day_ref][key] += int ( r.value  )
              
        # Loop through each day in interval_totals and add a key to the lookup and the values to a list
        for day_ref in interval_totals:

            # Check that all the values are not -1 null
            if sum(interval_totals[day_ref].values()) >  -1 * (24 / interval_hours):
                pro_list_lookup.append( day_ref )
                processing_list.append( interval_totals[day_ref].values() )

        # If the processing list is empty
        if len(processing_list) == 0:
            data['messages'].append('No data in processing list')
            return data

        # Cluster data
        print >>sys.stderr, '>>>> Starting Clustering'
        x = np.array(processing_list)
        if data['vis_settings']['dist_mode'] != '':
            y = pdist(x, data['vis_settings']['dist_mode'])
        else:
            y = pdist(x)
       
        z = linkage(y)
        root = to_tree(z)
        clusters = get_clusters(clusters_requires, root)

    
        # Convert to calendar format
        dates_to_cluster     = {}
        cluster_number       = 0
        day_pattern          = []
        
        # Check there are clusters
        if len(clusters) == 0:
            data['messages'].append('No clusters returned')
            return data

        # Start
        print >>sys.stderr, '>>>> Converting Clustering To Day Values'
        for cluster in clusters:
            cluster_number += 1
            for i in cluster:
                # Label each date with a cluster number
                dates_to_cluster[pro_list_lookup[i]] = cluster_number
                day_vals = []
                for p in range(0, 24/interval_hours):
                    day_vals.append(interval_totals[pro_list_lookup[i]][p])
                try:
                    day_pattern[cluster_number-1] = map(merger, day_pattern[cluster_number-1], day_vals)
                except IndexError:
                    day_pattern.append(day_vals)
       
        # Add data for calendar
        print >>sys.stderr, '>>>> Adding Dates to Calendar data'
        cluster_number = 0
        for d in day_pattern:
            cluster_number += 1
            data['patterns']['data'].append({
                'name': 'Cluster '+str(cluster_number),
                'cluster_count':cluster_number,
                'data': d
            })
    
        tmpdata = {}
        tmpdata['showname']            = 'Test'
        tmpdata['daytotals']           = dates_to_cluster

        data['sets'].append(tmpdata);
        data['highest'] = clusters_requires
        data['lowest']  = 1
       
        data['earliest_year']     = start.year
        data['most_recent_year']  = end.year

        return data


def get_clusters(desired_no_clusters, root):

    clusters = []
    t = root.dist

    print >>sys.stderr, '>>>> t', t

    # Err is the difference between what we want and what we get
    err     = abs(len(clusters) - desired_no_clusters)
    prev_ts = []
    # while err > desired_no_clusters / 10.0 and err not in prev_ts:
    while err > desired_no_clusters / 10.0:

        if len(clusters) > desired_no_clusters:
            t = t + t/2
        elif len(clusters) < desired_no_clusters:
            t = t - t/2
        else:
            return clusters
        
        clusters = collect_clusters(root, t)
        
        prev_ts.append(err)
        err = abs(len(clusters) - desired_no_clusters)

    return clusters




def collect_clusters(n, threshold):
    if n.dist < threshold or n.is_leaf():
        ids = collect_leaves(n)
        ids.sort()
        return [ids]
    else:
        l = n.get_left()
        r = n.get_right()
        l_cluster = collect_clusters(l, threshold)
        r_cluster = collect_clusters(r, threshold)
        result = []
        if issubclass(l_cluster[0].__class__, [].__class__):
            result += l_cluster
        else:
            result.append(l_cluster)
        if issubclass(r_cluster[0].__class__, [].__class__):
            result += r_cluster
        else:
            result.append(r_cluster)
        return result

def collect_leaves(n):
    if n.is_leaf():
        return [n.id,]
    else:
        l = n.get_left()
        r = n.get_right()
        left_leaves = collect_leaves(l)
        right_leaves = collect_leaves(r)
        return left_leaves + right_leaves

def merger(x,y): return (x + y) / 2

# -----------------------------------------------------------------------------

      











# ----------------------------------------------------------------------------- 
# CHART  - Time Series
# -----------------------------------------------------------------------------

def build_data_time(vis):
    
    data = {}
    data['vis_settings'] = vis.get_settings()

    data['data']     = {}
    data['chart']    = { 'zoomType':'x', 'type': data['vis_settings']['type'], 'height':700 }
    data['title']    = { 'text': str(vis.name) }
    data['xAxis']    = { 'type':'datetime' }
    data['legend']   = { 'layout':'vertical' }
    data['series']   = []
    data['yAxis']    = []
    data['messages'] = []

    # Work out the accesses needed
    axisMapping = {}
    op = 1
    
    for c in vis.get_all_channels():
        if not c.unit in axisMapping: 
            data['yAxis'].append({ 
                'oposite': op, 
                'labels': { 
                    'format':'{value}'+str(c.unit), 
                },
                'title': { 
                        'text':str(c.unit)
                }
            })
            axisMapping[c.unit] = len(data['yAxis']) - 1 
            op = 0

    # For each sensor add channel data
    for visin in vis.get_all_inputs():
        
        # Load and process the readings
        input_data = visin.get_readings()

        if not input_data:
            data['messages'].append('[ NO READINGS ] Check that interval is not too low -  '+visin.sensor.name+' '+visin.channel.name);
            continue

        tmp_output_list = []
        for r in input_data['readings']: 
            ts = time.mktime(r['interval_start'].timetuple()) * 1000
            tmp_output_list.append( [ts, r['value']] )
        
        # Sort results (Highcharts needs them in order!)
        tmp_output_list.sort(key=lambda x: x[0])
         
        if len(tmp_output_list) > 0:
            data['series'].append({ 
                  'name': input_data['name'],
                  'data': tmp_output_list,
                  'yAxis': axisMapping[visin.channel.unit],
                  'tooltip': { 
                    'valueSuffix': str(visin.channel.unit),
                    'headerFormat': ''
                  }
            })
        else:
            data['messages'].append('[ NO DATA ] ' + input_data['name']);

    # Sorting means you can use the name to ensure the colour stays consitant
    data['series'] = sorted(data['series'], key=lambda k: k['name'], reverse=True) 
    
    # Return the data
    return data










# ----------------------------------------------------------------------------- 
# CHART - Scatter
# -----------------------------------------------------------------------------

def build_data_scatter(vis):
    
    data = {}
    data['vis_settings'] = vis.get_settings()

    data['messages'] = []
    data['series']   = []
    data['tooltip_extra'] = {}

    # For each sensor add channel data
    inputs = list(vis.get_all_inputs())
    
    if len(inputs) % 2 != 0:
        data['messages'].append("Inputs must be in pairs of 2");
        return data

    counter = 0

    for i in range(0,len(inputs), 2):

        x_visin = inputs[i]
        y_visin = inputs[i+1]

        # Load readings
        x_data = x_visin.get_readings()
        y_data = y_visin.get_readings()

        # Format data fo x
        x_by_time = {}
        for x in x_data['readings']:
            ts = int(time.mktime(datetime.strptime(x['interval_start'].strftime('%Y-%m-%d'), '%Y-%m-%d').timetuple())) * 1000
            x_by_time[ts] = x['value']

        # Format data for y
        y_by_time = {}
        for y in y_data['readings']:
            ts = int(time.mktime(datetime.strptime(y['interval_start'].strftime('%Y-%m-%d'), '%Y-%m-%d').timetuple())) * 1000
            y_by_time[ts] = y['value']

        # Build channel name
        namestr = ''
        if x_visin.name != '' and y_visin.name != '':
            namestr = x_visin.name+' against '+y_visin.name,
        else:
            namestr = x_visin.sensor.name + ' ' +x_visin.channel.name + ' against ' + y_visin.sensor.name + ' ' + y_visin.channel.name

        # Cross x and y to build combined data
        compiled_data = []
        for xk in x_by_time:
            if xk in y_by_time:
                compiled_data.append({
                    'x': x_by_time[xk], 
                    'y':y_by_time[xk], 
                    'name':  datetime.fromtimestamp(int(xk/1000)).strftime('%Y-%m-%d %H:%M:%S')
                })

        tmp_colors = ['#50B432', '#ED561B', '#FF9933', '#3333FF', '#24CBE5', '#64E572', 
                 '#FF9655', '#FFF263', '#6AF9C4'] 

        # Add series
        if len(compiled_data) > 0:
            data['series'].append({ 
                'regression': True ,
                'regressionSettings': {
                    'type': 'linear',
                    'color':  tmp_colors[counter]
                },
                'name': namestr,
                'data': compiled_data,
                'color':  tmp_colors[counter],
                'counter': counter
            })

            counter += 1   

        else: 
            data['messages'].append('[ NO DATA ] ' + x_visin.sensor.name + ' and ' + y_visin.sensor.name);

        


    if len(inputs) > 0:
        data['xUnit']    = x_visin.channel.unit   
        data['xChannel'] = x_visin.channel.name 
        data['yUnit']    = y_visin.channel.unit  
        data['yChannel'] = y_visin.channel.name 
        data['xAxis'] = {
            'title': {
                'enabled': 1,
                'text': x_visin.channel.name + ' ' + x_visin.channel.unit
            }
        }
        data['yAxis'] = {
            'title': {
                'enabled': 1,
                'text': y_visin.channel.name + ' ' + y_visin.channel.unit
            }
        }

    # # Return the data
    return data







