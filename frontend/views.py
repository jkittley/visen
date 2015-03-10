#encoding:UTF-8
import time, json, math, calendar
from datetime import datetime, date, timedelta

from django.shortcuts import render
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from sd_store.models import *
from frontend.models import *
from frontend.forms import *
from databuild import *

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ----------------------------------------------------------------------------- 
# CHART DATE - Index
# -----------------------------------------------------------------------------

@login_required
def index(request):
 
    unique_groups = {}
    for vis in Visualisation.objects.all():
        if vis.group not in unique_groups:
            
            if vis.chart.name not in unique_groups:
                unique_groups[vis.chart.name] = {}

            if vis.group not in unique_groups[vis.chart.name]:
                unique_groups[vis.chart.name][vis.group] = []

        if vis.cache != '':
            cached = True
        else:
            cached = False
        
        start, end = vis.get_input_tme_span()
        if start != None and end != None:
            s_date = start.strftime("%d/%m/%Y")
            e_date = end.strftime("%d/%m/%Y")
        else:
            s_date = 'Unknown'
            e_date = 'Error'
            
        unique_groups[vis.chart.name][vis.group].append({  
            'name': vis.name,
            's_date': s_date,
            'e_date': e_date,
            'cached': cached,
            'pk' : vis.pk
        })

       
    context = RequestContext(request, { 
        'groups': unique_groups
    })

    return render_to_response('frontend/index.html',context_instance=context)



# ----------------------------------------------------------------------------- 
# Raw
# -----------------------------------------------------------------------------

@login_required
def raw(request):
    data  = None
    sensor = None
    channel = None
    start = "2014-01-01 00:00:00"
    end   = "2014-02-01 23:59:59"
    if request.method == "POST":
        sensor  = Sensor.objects.all().get(pk=request.POST.get('sensor')) 
        channel = Channel.objects.all().get(pk=request.POST.get('channel')) 
        start  = request.POST.get('start')
        end    = request.POST.get('end') 
        tstart = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        tend   = datetime.strptime(end,   '%Y-%m-%d %H:%M:%S')  
        data = SensorReading.objects.filter(sensor=sensor, channel=channel, timestamp__range=(tstart, tend))

    allsensors  = Sensor.objects.all().order_by('name')
    context = RequestContext(request, {
        'sensor':sensor,
        'channel':channel,
        'allsensors': allsensors,
        'start': start,
        'end': end,
        'data': data
    })
    return render_to_response('frontend/raw.html',context_instance=context)


# ----------------------------------------------------------------------------- 
# Help
# -----------------------------------------------------------------------------

@login_required
def help(request):
    context = RequestContext(request, { })
    return render_to_response('frontend/help.html',context_instance=context)


# ----------------------------------------------------------------------------- 
# GET DATA - USED BY VIEW AND AJAX
# -----------------------------------------------------------------------------

@login_required
def get_build_data(request, vis):
    # Check cache for data
    if vis.cache == '' or vis.cache == None:
        tmp_data  = build_data(vis)
        json_str  = json.dumps(tmp_data)
        if tmp_data != None:
            vis.cache = json_str
        vis.save()
    else:
        json_str = vis.cache
    return json_str



# ----------------------------------------------------------------------------- 
# View
# -----------------------------------------------------------------------------

def view(request, vispk):
    vis = Visualisation.objects.get(pk=vispk)   

    start, end = vis.get_input_tme_span()
    
    if start != None and end != None:
        s_date = start.strftime("%d/%m/%Y")
        e_date = end.strftime("%d/%m/%Y")
    else:
        s_date = None
        e_date = None

    json_str = get_build_data(request, vis)
    context = RequestContext(request, { 
        'vis'  : vis,
        's_date' : s_date,
        'e_date' : e_date,
        'data' : json_str
    })
    return render_to_response('frontend/chart_'+vis.chart.ref+'.html',context_instance=context)

# ----------------------------------------------------------------------------- 
# Ajax
# -----------------------------------------------------------------------------

def ajax(request, vispk):
    vis = Visualisation.objects.get(pk=vispk)      
    json_str = get_build_data(request, vis)
    return HttpResponse(json.dumps(json_str), content_type="application/json")

# ----------------------------------------------------------------------------- 
# Clear the cache
# -----------------------------------------------------------------------------

@login_required
def clear_cache(request, vispk):
    vis = Visualisation.objects.get(pk=vispk)    
    vis.cache = ''
    vis.save()  
    return HttpResponseRedirect('/view/'+str(vis.pk)) 




# ----------------------------------------------------------------------------- 
# Sensor Info
# -----------------------------------------------------------------------------

def sensor_info(request):
    unique_words = {}
    profiles = Sensor_profile.objects.all()
    for sp in profiles:
        for word in sp.longname.split():
            w = str(word).lower()
            if w in unique_words:
                unique_words[w] += 1
            else:
                unique_words[w] = 1

    out_words = []
    for w in unique_words:
        out_words.append({ 'name': w, 'count':unique_words[w], 'gas_total':0, 'elec_total':0 })

    # out_words.sort(key=lambda x: x['count'], reverse=True)

    context = RequestContext(request, { 'unique_words':out_words })
    return render_to_response('frontend/sensors.html',context_instance=context)

# ----------------------------------------------------------------------------- 
# Edit
# -----------------------------------------------------------------------------

@login_required
def edit(request, vispk):

    if vispk == 'new':
        chart = Chart.objects.all().get(ref='time')
        vis   = Visualisation(name='No name', chart=chart)
        vis.save()
        return HttpResponseRedirect('/edit/'+str(vis.pk)) 
    
        
    vis         = Visualisation.objects.get(pk=vispk) 
    inputs      = VisInput.objects.filter(vis=vis)
    allchannels = Channel.objects.all()
    allsensors  = Sensor.objects.all()
    settings    = vis.get_settings()

    if request.method == 'POST':
        
        section = request.POST.get('section')
        
        # Update basics
        if section == '1':
            vis.name         = request.POST.get('name')
            vis.group        = request.POST.get('group')
            newchart         = Chart.objects.all().get(pk=request.POST.get('charttype'))
            if newchart != vis.chart:
                vis.chart = newchart
                vis.setting = ''
            vis.cache = ''
            vis.save()
            
        # Update settings
        if section == '2':
            new_settings = {}
            for setting in settings:
                new_settings[setting] = request.POST.get('setting_'+setting)
            vis.settings = json.dumps(new_settings)
            vis.cache = ''
            vis.save()
           
    # Reload incase they have changed
    settings = vis.get_settings()
    inputs   = vis.get_all_inputs()
    charts   = Chart.objects.all()
    context  = RequestContext(request, { 
        'vis'  : vis,
        'inputs' : inputs,
        'settings': settings,
        'charts': charts
    })
    return render_to_response('frontend/edit.html',context_instance=context)




# ----------------------------------------------------------------------------- 
# Add / Edit VisInput
# -----------------------------------------------------------------------------

@login_required
def edit_input(request, vispk, visinpk):

    vis = Visualisation.objects.get(pk=vispk) 

    if visinpk == 'new':
        sensor  = Sensor.objects.all()[0]
        now = datetime.now()
        ps = datetime(now.year, now.month, now.day, 0, 0) 
        pe = datetime(now.year, now.month, now.day, 23, 59, 59) + timedelta(days=30)
        visin   = VisInput(name='', vis=vis, sensor=sensor, channel=sensor.channels.all()[0], period_start=ps, period_end=pe)
        visin.save()
        return HttpResponseRedirect('/edit_input/'+str(vispk)+'/'+str(visin.pk)+'/')

    visin = VisInput.objects.get(pk=visinpk)

    if request.method == 'POST':
        start      = request.POST.get('start')
        end        = request.POST.get('end')
        visin.sensor       = Sensor.objects.all().get(pk=request.POST.get('sensor'))
        visin.channel      = Channel.objects.all().get(pk=request.POST.get('channel'))
        visin.summode      = request.POST.get('summode')
        visin.preprocess   = request.POST.get('preprocess')
        visin.name         = request.POST.get('name')
        tmp_int = int(request.POST.get('interval'))
        if tmp_int == 0:
            visin.interval     = request.POST.get('cust_interval')
        else:
            visin.interval     = tmp_int
        visin.period_start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        visin.period_end   = datetime.strptime(end,   '%Y-%m-%d %H:%M:%S')
        visin.save();
        vis.cache = ''
        vis.save()
        return HttpResponseRedirect('/edit/'+str(vispk))

    

    context = RequestContext(request, { 
        'vis'  : vis,
        'visin': visin,
        'allsensors': Sensor.objects.all().order_by('name')
    })
    return render_to_response('frontend/edit_input.html',context_instance=context)


# ----------------------------------------------------------------------------- 
# Ajax get channels for a sensor
# -----------------------------------------------------------------------------

@login_required
def get_channels(request, sensorpk):
    sensor = Sensor.objects.get(pk=sensorpk)
    chlist = []
    for channel in sensor.channels.all():
        chlist.append({ 'name': channel.name, 'pk': channel.pk })
    return HttpResponse(json.dumps(chlist))

# ----------------------------------------------------------------------------- 
# Delete a Input
# -----------------------------------------------------------------------------

@login_required
def delete_input(request, vispk, visinpk):
    visin = VisInput.objects.get(pk=visinpk)
    visin.delete()
    return HttpResponseRedirect('/edit/'+str(vispk))























def add_months(sourcedate,months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year,month)[1])
    return date(year,month,day)

# ----------------------------------------------------------------------------- 
# Create vis inputs
# -----------------------------------------------------------------------------

def add_vis_input(vis, sensor, channel, start, end, name=None, summode=0, interval=None):
    if channel in sensor.channels.all():
        tmp = VisInput(vis=vis, sensor=sensor, channel=channel, period=True, period_start=start, period_end=end, summode=summode)
        if name:
            tmp.name = name
        if interval:
            tmp.interval = interval
        tmp.save()
        return True
    else:
        return False

# ----------------------------------------------------------------------------- 
# Create basic data and visualisation
# -----------------------------------------------------------------------------
 
def init(request):

    report = []

    # Delete All
    charts = Chart.objects.all()
    for c in charts:
        c.delete()


    # Build charts
    default_settings  = json.dumps({})
    chart_box,          created = Chart.objects.get_or_create(name='Box Plot', ref='box', min_inputs=1, max_inputs=50, default_settings=default_settings )
    
    default_settings  = json.dumps({ 'scale_global': True, })
    chart_cal,          created = Chart.objects.get_or_create(name='Calendar', ref='calendar', min_inputs=1, max_inputs=100, default_settings=default_settings )
    
    default_settings = json.dumps({ 'type': 'line', })
    chart_time,         created = Chart.objects.get_or_create(name='Time Series', ref='time', min_inputs=1, max_inputs=100, default_settings=default_settings )
    
    default_settings = json.dumps({})
    chart_table,        created = Chart.objects.get_or_create(name='Table', ref='table', min_inputs=1, max_inputs=100, default_settings=default_settings )
    
    default_settings = json.dumps({})
    chart_scatter,      created = Chart.objects.get_or_create(name='Scatter', ref='scatter', min_inputs=2, max_inputs=100, default_settings=default_settings )
    
    default_settings = json.dumps({ 'interval_hours': 3, 'clusters_requires': 7, 'dist_mode':'' })
    chart_cal_cluster,  created = Chart.objects.get_or_create(name='Calendar Cluster', ref='calcluster', min_inputs=1, max_inputs=1, default_settings=default_settings )
    
    default_settings = json.dumps({ 'full_circle': True, 'width': 500, 'height': 500 })
    chart_star,         created = Chart.objects.get_or_create(name='Star', ref='star', min_inputs=1, max_inputs=100, default_settings=default_settings )
    
    default_settings = json.dumps({ 'width': 500, 'height': 500 })
    chart_histogram,    created = Chart.objects.get_or_create(name='Histogram', ref='histogram', min_inputs=1, max_inputs=100, default_settings=default_settings )

    # Build channels
    channel_gas  = Channel.objects.all().get(name='Gas')  
    channel_elec = Channel.objects.all().get(name='Electricity')  
    channel_temp = Channel.objects.all().get(name='Temp (Feels like)')  
    channel_open = Channel.objects.all().get(name__icontains='Opening')  
    seasons = get_season_dates(2014)






    # --------------------------------------------------------------------------------------------------
    # Line - Core buildings Electricity and Gas Over time
    # --------------------------------------------------------------------------------------------------
    

    for sitetype in ['library','leisure']:
        for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            for m in [12,1,2,3,4,5,6,7,9,9,10,11]:
                if m == 12:
                    nm = 1
                    y = 2013
                else:
                    nm = m+1
                    y = 2014



                start   = datetime.strptime(str('1-'+str(m)+'-'+str(y)), "%d-%m-%Y")
                end     = datetime.strptime(str('1-'+str(nm)+'-'+str(y)), "%d-%m-%Y")

                sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
                for sprofile in sensors_profiles:
                    
                    vis, created = Visualisation.objects.get_or_create(name=sprofile.longname+' '+chdata[0]+' '+str(m)+'/'+str(y), group=chdata[0]+' Vs Opening Hours', chart=chart_time)
                    if created:
                        add_vis_input(vis, sprofile.sensor, chdata[1],    start, end, name=None, summode=0, interval=3600)
                        add_vis_input(vis, sprofile.sensor, channel_open, start, end, name=None, summode=0, interval=3600)



    # --------------------------------------------------------------------------------------------------
    # Calendar Opening Hours 
    # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['library','leisure']:
    #     vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' Openning Hours', group='Calendar Opening Hours', chart=chart_cal)
    #     if created:
    #         vis.settings = json.dumps({
    #         'width': 300,
    #         'height': 300
    #         })
    #         vis.save()
    #         sensors_profiles = Sensor_profile.objects.filter(longname__icontains=sitetype) 

    #         for sprofile in sensors_profiles:
    #             add_vis_input(vis, sprofile.sensor, channel_open, start, end, None, 0, -1)



    # --------------------------------------------------------------------------------------------------
    # Calendar for comapring each site type 
    # --------------------------------------------------------------------------------------------------
    start   = seasons['winter']['start']
    end     = seasons['autumn']['end']

    for sitetype in ['depot','library','leisure']:
        for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:  
            vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' - '+chdata[0], group='Calendar Compare Sites Winter 13 to Autumn 14', chart=chart_cal)
            if created:
                vis.settings = json.dumps({
                'width': 300,
                'height': 300,
                'scale_global': False
                })
                vis.save()
                sensors_profiles = Sensor_profile.objects.filter(longname__icontains=sitetype) 
                for sprofile in sensors_profiles:
                    add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, -1)


    # # --------------------------------------------------------------------------------------------------
    # # Calendar of multiple sites, but with own colour coding range
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:  
    #         vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' - '+chdata[0], group='Calendar Sites Local Coloring Winter 13 to Autumn 14', chart=chart_cal)
    #         if created:
    #             vis.settings = json.dumps({
    #                 'scale_global': False
    #             })
    #             vis.save()
    #             sensors_profiles = Sensor_profile.objects.filter(longname__icontains=sitetype) 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, -1)



    # # --------------------------------------------------------------------------------------------------
    # # Calendar for each building 
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # sensors_profiles = Sensor_profile.objects.all().filter(Q(longname__icontains='depot') | Q(longname__icontains='library') |  Q(longname__icontains='leisure'))
    # for sprofile in sensors_profiles:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:  
    #         vis, created = Visualisation.objects.get_or_create(name=sprofile.longname.capitalize()+' - '+chdata[0]+'', group='Calendar Idv Site Winter 13 to Autumn 14', chart=chart_cal)
    #         if created:
    #             add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, -1)


    # # --------------------------------------------------------------------------------------------------
    # # Cluster Calendar - Core Sites (Plot per Site)
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # sensors_profiles = Sensor_profile.objects.all().filter(Q(longname__icontains='depot') | Q(longname__icontains='library') |  Q(longname__icontains='leisure'))
    # for sprofile in sensors_profiles:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
    #         vis, created = Visualisation.objects.get_or_create(name=sprofile.longname+' '+chdata[0], group='Cluster Calendar 2014', chart=chart_cal_cluster)
    #         if created:
    #             vis.save()
    #             add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, -5)



    # # --------------------------------------------------------------------------------------------------
    # # Histograms - Core Sites together
    # # --------------------------------------------------------------------------------------------------
    start   = seasons['winter']['start']
    end     = seasons['autumn']['end']

    for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
        vis, created = Visualisation.objects.get_or_create(name='All Core Sites - '+chdata[0], group='Histograms Core Sites W 2013 to A 2014', chart=chart_histogram)
        if created:
            sensors_profiles = Sensor_profile.objects.all().filter(Q(longname__icontains='depot') | Q(longname__icontains='library') |  Q(longname__icontains='leisure'))   
            for sprofile in sensors_profiles:
                add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, -8)


    # # --------------------------------------------------------------------------------------------------
    # # Histograms - Core Sites Seporatly
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
    #         vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' - '+chdata[0]+' Winter 2013 to Autumn 2014', group='Histograms Individual W 2013 to A 2014', chart=chart_histogram)
    #         if created:
    #             vis.settings = json.dumps({
    #                 'width': 300,
    #                 'height': 300
    #             })
    #             vis.save()
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, -8)



    # # --------------------------------------------------------------------------------------------------
    # # Scatter Gas Electric Colloration Chart - Core Sites 
    # # --------------------------------------------------------------------------------------------------
    
    # sensors_profiles = Sensor_profile.objects.all().filter(Q(longname__icontains='depot') | Q(longname__icontains='library') |  Q(longname__icontains='leisure'))   
    # for sprofile in sensors_profiles:
    #     vis, created = Visualisation.objects.get_or_create(name=sprofile.longname+' Correlation Winter 2013 to Autumn 2014', group='Scatter Gas Electric Correlation', chart=chart_scatter)
    #     if created:
    #         vis.settings = json.dumps({
                
    #         })
    #         vis.save()
    #         for season in ['spring','summer','autumn','winter']:
    #             if channel_elec in sprofile.sensor.channels.all():
    #                 if channel_gas in sprofile.sensor.channels.all():
    #                     add_vis_input(vis, sprofile.sensor, channel_elec, seasons[season]['start'], seasons[season]['end'], season.capitalize()+' Electricity' , 0, -1)
    #                     add_vis_input(vis, sprofile.sensor, channel_gas,  seasons[season]['start'], seasons[season]['end'], season.capitalize()+' Gas' , 0, -1)


    # # --------------------------------------------------------------------------------------------------
    # # Scatter Gas Temp Colloration Chart - Core Sites 
    # # --------------------------------------------------------------------------------------------------
    
    # sensors_profiles = Sensor_profile.objects.all().filter(Q(longname__icontains='depot') | Q(longname__icontains='library') |  Q(longname__icontains='leisure'))   
    # for sprofile in sensors_profiles:
    #     vis, created = Visualisation.objects.get_or_create(name=sprofile.longname+' Correlation Winter 2013 to Autumn 2014', group='Scatter Gas Temperature Correlation', chart=chart_scatter)
    #     if created:
    #         vis.settings = json.dumps({
              
    #         })
    #         vis.save()
    #         for season in ['spring','summer','autumn','winter']:
    #             if channel_temp in sprofile.sensor.channels.all():
    #                 if channel_gas in sprofile.sensor.channels.all():
    #                     add_vis_input(vis, sprofile.sensor, channel_temp, seasons[season]['start'], seasons[season]['end'], season.capitalize()+' Temperature' , 1, -1)
    #                     add_vis_input(vis, sprofile.sensor, channel_gas,  seasons[season]['start'], seasons[season]['end'], season.capitalize()+' Gas' , 0, -1)



    # # --------------------------------------------------------------------------------------------------
    # # Star Chart - Core Sites Day Patterns (3 hour intervals)
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            
    #         # Day patterns
    #         vis, created = Visualisation.objects.get_or_create(name='Day patterns '+sitetype.capitalize()+' '+chdata[0]+' 2014 (3hr intervals)', group='Day Patterns (3hr intervals) 2014', chart=chart_star)
    #         if created:
    #             vis.settings = json.dumps({
    #                 'full_circle': True,
    #                 'width': 300,
    #                 'height': 300
    #             })
    #             vis.save()
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, 10800)



    # # --------------------------------------------------------------------------------------------------
    # # Star Chart - Core Sites Day Patterns (1 hour intervals)
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            
    #         # Day patterns
    #         vis, created = Visualisation.objects.get_or_create(name='Day patterns '+sitetype.capitalize()+' '+chdata[0]+' 2014 (1hr intervals)', group='Day Patterns (1hr intervals) 2014', chart=chart_star)
    #         if created:
    #             vis.settings = json.dumps({
    #                 'full_circle': True,
    #                 'width': 300,
    #                 'height': 300
    #             })
    #             vis.save()
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, 3600)



    # # --------------------------------------------------------------------------------------------------
    # # Star Chart - Core Sites Seasonal
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            
    #         # Seasonal patterns
    #         vis, created = Visualisation.objects.get_or_create(name='Seasonal '+sitetype.capitalize()+' '+chdata[0]+' Winter 2013 to Autumn 2014', group='Star Seasonal Patterns', chart=chart_star)
    #         if created:
    #             vis.settings = json.dumps({
    #                 'full_circle': True,
    #                 'width': 300,
    #                 'height': 300
    #             })
    #             vis.save()
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, -4)



    # # --------------------------------------------------------------------------------------------------
    # # Star Plots - Core buildings Gas - Seasonal - Weekend Vs Weekday - Central Tendancy
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            
    #         vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' Buildings '+chdata[0]+' Winter 2013 - Autumn 2014', group='Seasonal Weekday Weekend Central Tendancy', chart=chart_star)
    #         vis.settings = json.dumps({
    #                 'full_circle': True,
    #                 'width': 300,
    #                 'height': 300
    #         })
    #         if created:
    #             vis.save()
    #             unique_postcodes = []
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             # Build list of unique postcodes 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 0, -7)


    # # --------------------------------------------------------------------------------------------------
    # # Star Plots - Core buildings Gas - Seasonal - Weekend Vs Weekday - IQR Spread
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']
    
    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            
    #         vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' Buildings '+chdata[0]+' 2014', group='Seasonal Weekday Weekend IQR Spread', chart=chart_star)
    #         vis.settings = json.dumps({
    #                 'full_circle': True,
    #                 'width': 300,
    #                 'height': 300
    #         })
    #         if created:
    #             vis.save()
    #             unique_postcodes = []
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             # Build list of unique postcodes 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end, None, 7, -7)




    # # --------------------------------------------------------------------------------------------------
    # # Line - Gas Against Weather for core sites
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # unique_postcodes = []
    # sensors_profiles = Sensor_profile.objects.all().filter(Q(longname__icontains='depot') | Q(longname__icontains='library') |  Q(longname__icontains='leisure'))
   
    # # Build list of unique postcodes 
    # for sprofile in sensors_profiles:
    #     if sprofile.postcode != '':
    #         pc = sprofile.postcode.split()[0]
    #         if pc not in unique_postcodes:
    #             unique_postcodes.append(pc)

    # # For each postcode
    # for pc in unique_postcodes:
        
    #     # Line in Temp
    #     vis, created = Visualisation.objects.get_or_create(name='Core Buildings in '+pc+' 2014', group='Gas VS Outdoor Temp', chart=chart_time)
    #     if created:
    #         vis.save()
            
    #         sensors_profiles = Sensor_profile.objects.all().filter(postcode__icontains=pc+' ').filter(Q(longname__icontains='depot') | Q(longname__icontains='library') |  Q(longname__icontains='leisure'))
    #         first = True
    #         for sprofile in sensors_profiles:
    #             add_vis_input(vis, sprofile.sensor, channel_gas, start, end)
    #             if first:
    #                 add_vis_input(vis, sprofile.sensor, channel_temp, start, end, '[ '+pc+' Temp ]', 1)
    #                 first = False
   

    #     # Calendar compare
    #     vis, created = Visualisation.objects.get_or_create(name='Core Buildings in '+pc+' 2014', group='Gas Comparison In Postcode Areas', chart=chart_cal)
    #     if created:
    #         vis.save()
    #         sensors_profiles = Sensor_profile.objects.all().filter(postcode__icontains=pc+' ').filter(Q(longname__icontains='depot') | Q(longname__icontains='library') |  Q(longname__icontains='leisure')) 
    #         for sprofile in sensors_profiles:
    #             add_vis_input(vis, sprofile.sensor, channel_gas, start, end)
               


    # # --------------------------------------------------------------------------------------------------
    # # Line - Core buildings Electricity and Gas Over time
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            
    #         vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' Buildings '+chdata[0]+' 2014', group='Core Comparisions', chart=chart_time)
    #         if created:
    #             unique_postcodes = []
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             # Build list of unique postcodes 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end)


    # # --------------------------------------------------------------------------------------------------
    # # Box Plots - Core buildings Electricity and Gas - Weekend Vs Weekday
    # # --------------------------------------------------------------------------------------------------
    # start   = seasons['winter']['start']
    # end     = seasons['autumn']['end']

    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            
    #         vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' Buildings '+chdata[0]+' 2014', group='Weekday vs Weekend Comparisions', chart=chart_box)
    #         if created:
    #             unique_postcodes = []
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             # Build list of unique postcodes 
    #             for sprofile in sensors_profiles:
    #                 add_vis_input(vis, sprofile.sensor, chdata[1], start, end, '', 0, -6)



    # # --------------------------------------------------------------------------------------------------
    # # Box Plots - Core buildings Electricity and Gas - Seasonal - Weekend Vs Weekday
    # # --------------------------------------------------------------------------------------------------
    # for sitetype in ['depot','library','leisure']:
    #     for chdata in [['Electricity', channel_elec], ['Gas', channel_gas]]:
            
    #         vis, created = Visualisation.objects.get_or_create(name=sitetype.capitalize()+' Buildings '+chdata[0]+' 2014', group='Seasonal + Weekday vs Weekend Comparisions', chart=chart_box)
    #         if created:
    #             unique_postcodes = []
    #             sensors_profiles = Sensor_profile.objects.all().filter(longname__icontains=sitetype) 
    #             # Build list of unique postcodes 
    #             for sprofile in sensors_profiles:
    #                 start   = datetime.strptime('Dec 31 2013 00:00:00', '%b %d %Y %H:%M:%S')
    #                 for season in ['Winter','Spring','Summer','Autumn']:
    #                     end = add_months(start, 3)
    #                     add_vis_input(vis, sprofile.sensor, chdata[1], start, end, season+' '+sprofile.longname, 0, -6)
    #                     start = end



    # ----------------------------------------------------------------------------- 
    # Clean up
    # -----------------------------------------------------------------------------

    for vis in Visualisation.objects.all():
        num_ins = VisInput.objects.filter(vis=vis).count()
        report.append(vis.name+' has '+str(num_ins)+' inputs')
        if num_ins == 0:
            report.append('-- '+vis.name+' has been deleted')
            vis.delete()

    report.append('Init Complete')
    outstr = ''
    for l in report:
        outstr += l + '<BR>'
    return HttpResponse(outstr);

















# ----------------------------------------------------------------------------- 
# Funstion uses googles geocoding service to get the lnglat for each site based 
# on the postcode tool_geocoder.html contains the javascrip side
# -----------------------------------------------------------------------------

def addgeodata(request):
    if request.method == 'POST': 
        try:
            pk   = int(request.POST.get('pk'))
        except:
            return HttpResponse('PK Failed')
        try:
            lon  = float(request.POST.get('lon'))
        except:
            return HttpResponse('Lon Failed')
        try:
            lat  = float(request.POST.get('lat'))
        except:
            return HttpResponse('Lat Failed')
        try:
            sp   = Sensor_profile.objects.all().get(pk=pk);
        except:
            return HttpResponse('SP Failed')
        sp.lon = lon
        sp.lat = lat
        sp.save()
        return HttpResponse('Geocoding Complete -- pk:'+ str(pk) +' - lon:'+ str(lon)+' - lat:'+ str(lat) +'');
    else:
        context = RequestContext(request, {})
        return render_to_response('frontend/tool_geocoder.html',context_instance=context)
    










