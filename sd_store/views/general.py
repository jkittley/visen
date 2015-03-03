#encoding:UTF-8
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect,\
    HttpResponseNotAllowed, Http404
from django.contrib.auth import authenticate, login, logout
from django.utils import simplejson as json
from datetime import datetime
from django.views.decorators.http import require_GET, require_POST
from basicutils.decorators import access_required
from django.db.transaction import commit_on_success

from .. import sdutils
from time import mktime
from django.db.models import Min, Max

from basicutils import djutils
from django.contrib.auth.models import User
from ..models import Meter, MeteringPoint, EventType, StudyInfo, \
                     Sensor, Channel, SensorReading, UserProfile
from basicutils.djutils import to_dict

from django.core import serializers
from django.shortcuts import get_object_or_404
from sd_store.forms import RawDataForm, SampledIntervalForm
from sd_store.models import RawDataKey
from django.db.utils import IntegrityError
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from basicutils.decorators import log_request
from django.views.decorators.csrf import csrf_exempt
json_serializer = serializers.get_serializer("json")()

from logging import getLogger
logger = getLogger('custom')

JS_FMT = '%a %b %d %H:%M:%S %Y'

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        u = request.POST['username']
        p = request.POST['password']
        user = authenticate(username=u, password=p)
        if user != None:
            login(request, user)
            return HttpResponse(json.dumps({'status' : 'success', 'user_id' : user.id}))            
        else:
            return HttpResponseBadRequest(djutils.get_json_error(json.dumps({'status' : 'bad username or password'})))
    return HttpResponseBadRequest(djutils.get_json_error("NOT_POST_REQUEST"))

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(settings.LOGOUT_URL)

@csrf_exempt
@access_required
def meter_view(request, meter_id=None):
    if request.method == "GET":
        if meter_id == None:
            owner = djutils.get_requested_user(request)
            meter_list = Meter.objects.filter(user=owner)
            
            return HttpResponse(json.dumps([to_dict(x) for x in meter_list]))
        else:
            meter_list = (Meter.objects.get(id=meter_id),)
            if meter_list[0].user != djutils.get_requested_user(request):
                return HttpResponse("Tried to access a meter from a different user than the authenticated user.",status=403)
            return HttpResponse(json.dumps([to_dict(m) for m in meter_list]))
    elif request.method == "POST":
        raise NotImplementedError
    else:
        return HttpResponseBadRequest(djutils.get_json_error("NOT_GET_REQUEST"))

@csrf_exempt
@access_required
def sensor_view(request, sensor_id=None):
    if request.method == "GET":
        if sensor_id == None:
            owner = djutils.get_requested_user(request)
            sensor_list = Sensor.objects.filter(user=owner)
            return HttpResponse(json.dumps([to_dict(x) for x in sensor_list]))           
        else:
            try:
                sensor = Sensor.objects.get(id=sensor_id)
                if sensor.user != djutils.get_requested_user(request):
                    return HttpResponse("Tried to access a sensor from a different user than the authenticated user.",status=403)
                return HttpResponse(json.dumps(to_dict(sensor)))
            except Sensor.DoesNotExist:
                return HttpResponseNotFound("Sensor with id %s not found." % (sensor_id,))
    elif request.method == "POST": # Ideally would have this PUT, but urllib sucks...
        # POST all require these three parameters. Check they are present, else 400
        try:
            mac = unicode(request.POST["mac"])
            name = unicode(request.POST["name"])
            sensor_type = unicode(request.POST["sensor_type"])            
        except KeyError:
            return HttpResponseBadRequest("The request to sensor_view with the following parameters is invalid: " + repr(request))
        except ValueError:
            return HttpResponseBadRequest("The request to sensor_view had malformed parameters.")
        
        sensor_owner = djutils.get_requested_user(request)

        if sensor_id == None:
            # TODO: this should be replaced by dealing with Meter separately from Sensor

            # sensor_id being None may mean that the sensor was not created yet, or
            # a sync problem between the two servers. 
            # get or create a sensor with these params:
            sensor, _ = Sensor.objects.get_or_create(mac=mac, 
                                                   defaults={
                                                         'user': sensor_owner, 
                                                         'name': name, 
                                                         'sensor_type': sensor_type})
            
            profile = UserProfile.objects.get(user=sensor_owner)
            if profile.primary_sensor is None:
                if sensor.name.startswith(u'Meter Reader'):
                    profile.primary_sensor = sensor
                    profile.save()
            
            return HttpResponse(str(sensor.id),status=201)
        else: # Request to specific sensor_id       
            # If it exists already:    
            try:
                sensor = Sensor.objects.get(id=sensor_id)
            except Sensor.DoesNotExist: # If it doesn't exist, then throw 404
                return HttpResponseNotFound("The specified sensor does not exist: " + repr(sensor_id))

            # And doesn't belong to another user
            if sensor.user != sensor_owner:
                return HttpResponseForbidden("Tried to modify a sensor that doesn't belong the authenticated user.")    
            else:
                # Then we need to update it according to the request
                sensor.mac = mac
                sensor.sensor_type = sensor_type
                sensor.name = name
                try:
                    sensor.save()
                except IntegrityError as e:
                    # TODO: is this the best response
                    logger.warn('IntegrityError: %s' % (str(e)))
                    return HttpResponseForbidden("Sensor already exists.")
                return HttpResponse(str(sensor.id),status=200)

                
    elif request.method == "DELETE":
        if sensor_id == None:
            return HttpResponse("Not allowed to delete all sensors with a single call", status=403)
        user = djutils.get_requested_user(request)
        try:
            sensor = Sensor.objects.get(pk=sensor_id)
            if user != sensor.user:
                return HttpResponse("Cannot delete other users' meters!", status=403)
            else:
                with commit_on_success():
                    readings = SensorReading.objects.filter(sensor=sensor)
                    for reading in readings:
                        reading.delete()
                    sensor.delete()
                return HttpResponse("Sensor %s deleted." % (sensor_id,), status=200)
        except Sensor.DoesNotExist:
            return HttpResponseNotFound("Meter with id %s not found." % (sensor_id,))
    else:
        return HttpResponseBadRequest("The sensor_view is unable to handle the given HTTP method: " + repr(request.method))

@csrf_exempt
@access_required
def channel_view(request, sensor_id=None, channel_name=None):
    if request.method=='GET':
        user = djutils.get_requested_user(request)
        try:
            sensor = Sensor.objects.get(id=sensor_id)
            channel = sensor.channels.get(name=channel_name)
            if user != sensor.user:
                return HttpResponse("Tried to access another user's data. Forbidden.",status=403)
            return HttpResponse(json.dumps(to_dict(channel)))
                
        except Sensor.DoesNotExist:
            return HttpResponseNotFound()
        except Channel.DoesNotExist:
            return HttpResponseNotFound()
        
    elif request.method=='POST':
        user = djutils.get_requested_user(request)
        
        try:
            unit = unicode(request.POST['unit'])
            interval = int(request.POST['reading_frequency'])
        except KeyError:
            return HttpResponseBadRequest("POST to channel_view with missing parameters.")
        except ValueError:
            return HttpResponseBadRequest("POST to channel_view with malformed parameters.")
        
        try:
            sensor = Sensor.objects.get(id=sensor_id)
        except Sensor.DoesNotExist:
            return HttpResponse("Tried to append a channel to a non-existent sensor.", status=404)
        
        if user != sensor.user:
            logger.warn("Tried to add a channel to a different user's sensor. " + 'user: %s, sensor: %s, channel_name: %s' % (str(user), str(sensor), str(channel_name)))
            return HttpResponse("Tried to add a channel to a different user's sensor. Forbidden.", status=403)

        # Create the channel if needed.
        channel, _ = Channel.objects.get_or_create(name=channel_name,
                                                   unit=unit,
                                                   reading_frequency=interval)
        
        # If the sensor doesn't have a channel by that name, create it:
        if not bool(sensor.channels.filter(name=channel_name)):
            try:
                sensor.channels.add(channel)
                sensor.save()
                return HttpResponse("Added channel to sensor.", status=201)
            except IntegrityError as e:
                #msg = "exception from sensor.channels.add(channel): %s; " % str(e)
                #msg += "sensor.channels.all(): %s; " % str(sensor.channels.all())
                #msg += "IDs: %s; " % str([x.id for x in sensor.channels.all()])
                #msg += "new channel id: %s; " % str(channel.id)
                #msg += "bool(sensor.channels.filter(name=%s)): %s" % (
                #      channel_name, str(bool(sensor.channels.filter(name=channel_name))) )
                #logger.error(msg)
                return HttpResponse("Could not add channel to sensor.", status=201)
        else:
            oldChannel = sensor.channels.get(name=channel_name)
            sensor.channels.remove(oldChannel)
            sensor.save()
            sensor.channels.add(channel)
            sensor.save()
            return HttpResponse("Modified existing channel on sensor.", status=200)
        
    elif request.method=='DELETE':
        user = djutils.get_requested_user(request)
        try:
            sensor = Sensor.objects.get(id=sensor_id)
            channel = sensor.channels.get(name=channel_name)
            
            if user != sensor.user:
                return HttpResponse("Tried to delete another user's data. Forbidden.", status=403)
            
            with commit_on_success():
                for reading in SensorReading.objects.filter(sensor=sensor,channel=channel):
                    reading.delete()
                sensor.channels.remove(channel)
            return HttpResponse("Successfully removed channel.",status=200)
        except Sensor.DoesNotExist:
            return HttpResponse("Tried to delete a channel on a non-existent sensor.", status=404)
        except Channel.DoesNotExist:
            return HttpResponse("Tried to delete a non-existent channel.", status=404)
    else:
        return HttpResponseBadRequest("channel_view cannot serve HTTP %s." % (request.method,))

@csrf_exempt
@require_POST
def raw_data_view(request, sensor_mac, channel_name):
    # key: string
    # value: float
    
    # Get sensor and channel
    sensor = get_object_or_404(Sensor, mac=sensor_mac)
    try:
        channel = sensor.channels.get(name=channel_name)
    except Channel.DoesNotExist:
        return HttpResponseNotFound("This sensor does not appear to contain that channel.")
    
    form = RawDataForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(djutils.get_json_error(dict(form.errors)))
    dt = datetime.now()
    key_string = form.cleaned_data['key']
    value = form.cleaned_data['value']
    
    # check that the key matches the sensor
    try:
        key = RawDataKey.objects.get(value=key_string)
        if not sensor in key.sensors.all():
            return HttpResponse('Unauthorized', status=401)
    except RawDataKey.DoesNotExist:
        return HttpResponse('Unauthorized', status=401)
    
    reading, created = SensorReading.objects.get_or_create(sensor=sensor,
                                                           channel=channel,
                                                           timestamp=dt,
                                                           defaults={
                                                             'value': value})
    if not created:
        reading.value = value
        reading.save()
    return HttpResponse(djutils.get_json_success(True))

#@require_POST
@csrf_exempt
@commit_on_success
@access_required
def data_view(request, sensor_id=None, channel_name=None):
    if request.method == 'GET':
        # Get sensor and channel
        sensor = get_object_or_404(Sensor, id=sensor_id)
        try:
            channel = sensor.channels.get(name=channel_name)
        except Channel.DoesNotExist:
            return HttpResponseNotFound("This sensor does not appear to contain that channel.")
        
        # Check user has permission 
        if djutils.get_requested_user(request) != sensor.user:
            return HttpResponse("Attempted to edit another user's sensor. Forbidden.", status=403)
        
        # check the interval form
        form = SampledIntervalForm(request.GET)
        if not form.is_valid():
            return HttpResponseBadRequest(djutils.get_json_error(dict(form.errors)))
        
        requested_interval = form.cleaned_data['sampling_interval']
        start = form.cleaned_data['start']
        end = form.cleaned_data['end']
        
        if start >= end:
            return HttpResponseBadRequest(djutils.get_json_error('invalid interval requested'))
        
        # TODO: using 'power' here as an argument is a hack, it should be fixed
        reading_list = sdutils.filter_according_to_interval(sensor, channel, start, end, requested_interval, 'generic')
        
        result = {}
        result['data'] = [{'t': 1000 * mktime(x.timestamp.timetuple()), 
                           'value': x.value} for x in reading_list]
    
        if len(result['data']) == 0:
            #raise SensorReading.DoesNotExist('no sensor readings')
            result['max_datetime'] = 0 
            result['min_datetime'] = 0
            return HttpResponse(json.dumps(result))
            
        min_datetime = SensorReading.objects.filter(sensor=sensor, 
                                                    channel=channel
                        ).aggregate(Min('timestamp'))['timestamp__min']
        min_datetime = min_datetime.strftime(djutils.DATE_FMTS[0])
        result['min_datetime'] = min_datetime
        
        max_datetime = SensorReading.objects.filter(sensor=sensor, 
                                                    channel=channel
                        ).aggregate(Max('timestamp'))['timestamp__max']
        max_datetime = max_datetime.strftime(djutils.DATE_FMTS[0])
        result['max_datetime'] = max_datetime 
        
        return HttpResponse(json.dumps(result))
        
    elif request.method == 'POST':
        # TODO: this could be made more clean, using a multi-part post..
        # Check inputs are present and deserialisable
        try:
            data = json.loads(request.POST['data'])
        except KeyError:
            return HttpResponseBadRequest("The data is missing.")
        except TypeError:
            return HttpResponseBadRequest("The data is not a well formed JSON string.")
        
        # Get sensor and channel
        sensor = get_object_or_404(Sensor, id=sensor_id)
        try:
            channel = sensor.channels.get(name=channel_name)
        except Channel.DoesNotExist:
            return HttpResponseNotFound("This sensor does not appear to contain that channel.")
        
        # Check user has permission 
        if djutils.get_requested_user(request) != sensor.user:
            return HttpResponse("Attempted to edit another user's sensor. Forbidden.", status=403)
        
        # Add data - checking validity
        newCount = 0
        with commit_on_success():
            if type(data)!= list:
                return HttpResponseBadRequest("data_view requires a list of data points.")
            for datum in data:
                try:
                    timestamp = datetime.strptime(str(datum['timestamp']),JS_FMT)
                    value = float(datum['value'])
                except KeyError:
                    logger.error('error in data posted to sd_store')
                    return HttpResponseBadRequest("data_view requires data points to have a 'timestamp' and 'value' key.")
                except ValueError:
                    logger.error('error in data posted to sd_store (timestamp formatting?)')
                    return HttpResponseBadRequest("Timestamps must be formatted:"+JS_FMT+', and values must be floats.')
                
                reading, created = SensorReading.objects.get_or_create(sensor=sensor,
                                                                       channel=channel,
                                                                       timestamp=timestamp,
                                                                       defaults={'value': value})
                if not created:
                    reading.value = value
                    reading.save()
                if created:
                    newCount += 1
        return HttpResponse(str(newCount),status=200)
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])
    

@require_GET
@access_required    
def last_reading_view(request, sensor_id=None, channel_name=None):
    user = djutils.get_requested_user(request)
    
    sensor = get_object_or_404(Sensor, id=sensor_id)
    try:
        channel = sensor.channels.get(name=channel_name)
    except Channel.DoesNotExist:
        raise Http404('Requested channel does not exist.')
    
    if user != sensor.user:
        return HttpResponse("Tried to access data belonging to another user. Forbidden.", status=403)
    
    readings = SensorReading.objects.filter(channel=channel,sensor=sensor)
    
    if readings.exists():
        lastReadingTime = readings.order_by("-timestamp")[0].timestamp.strftime(JS_FMT)
        return HttpResponse(lastReadingTime)
    else:
        msg = 'sensor: %s, channel: %s, readings.count(): %d' % (
                 str(sensor), str(channel), readings.count())
        logger.info(msg)
        return HttpResponse(None)
        
@csrf_exempt
@access_required
def metering_point_view(request, metering_point_id=None):
    #log_request('metering_point_view %s'%(str(metering_point_id)), request)
    if request.method == "GET":
        if metering_point_id != None:
            metering_point = MeteringPoint.objects.get(id = metering_point_id)
            return HttpResponse(json.dumps(to_dict(metering_point))) 
        else:
            user = request.GET.get('user', request.user.id)
            metering_points = MeteringPoint.objects.filter(user=user)
            return HttpResponse(json.dumps([x.id for x in metering_points]))
    elif request.method == "POST":
        user = request.user.id
        if user != None:
            metering_point_name = request.POST.get('meteringPointName', None)
            metering_point_description = request.POST.get('meteringPointDescription', None)
            metering_point_meter = request.POST.get('meter', None)
            if Meter.objects.filter(mac = metering_point_meter).count() > 0:
                metering_point_meter = Meter.objects.get(mac = metering_point_meter)
            else:
                metering_point_meter = None
                
            metering_points = MeteringPoint.objects.filter(user = user)
            metering_point = None
            if metering_point_id != None:
                if metering_points.filter(id = metering_point_id).count() > 0:
                    metering_point = metering_points.get(id = metering_point_id)
                    metering_point.name = metering_point_name
                    metering_point.description = metering_point_description
                    metering_point.meter = metering_point_meter
                else:
                    return HttpResponseNotFound(djutils.get_json_error("NO_SUCH_METERING_POINT"))
            else:
                try:
                    metering_point = MeteringPoint(name = metering_point_name, description = metering_point_description, sensor = metering_point_meter, user = request.user)
                except:
                    return HttpResponseBadRequest(djutils.get_json_error('BAD_ARGS'))
            metering_point.save()
            return HttpResponse(djutils.get_json_success(metering_point.id))
        return HttpResponseNotFound(djutils.get_json_error("NO_SUCH_USER"))
    elif request.method == "DELETE":
        if MeteringPoint.objects.filter(id = metering_point_id).count() > 0:
            metering_point = MeteringPoint.objects.get(id = metering_point_id)
            if metering_point.id == request.user.id:
                metering_point_id = metering_point.id
                metering_point.delete()
                return HttpResponse(djutils.get_json_success(metering_point_id))
            return HttpResponse(djutils.get_json_error("ACCESS_DENIED"), status=403)
        return HttpResponseNotFound(djutils.get_json_error("NO_SUCH_METERING_POINT"))
    return HttpResponseBadRequest(djutils.get_json_error("NOT_GET_POST_OR_DELETE_REQUEST"))


@require_GET
def event_type_view(request, event_type_id=None):
    #log_request('event_type_view %s' % (event_type_id), request)
    
    if event_type_id != None:
        event = EventType.objects.get(id=event_type_id)
        return HttpResponse(json.dumps(to_dict(event)))
    else:
        events = EventType.objects.all().exclude(name__startswith='question')
        #return HttpResponse(utils.to_json_list(events))
        return HttpResponse(json.dumps([to_dict(x) for x in events]))


@access_required
@require_GET
def reference_consumption_view(request):
    #log_request('reference_consumption_view', request)

    owner_id = request.GET.get('user_id')
    if owner_id in (None, request.user.id):
        owner = request.user
    else:
        owner = User.objects.get(id=owner_id)
    
    # TODO: add a try except and return undefined if appropriate
    # filter the reading list for the selection period
    result = StudyInfo.objects.get(user=owner)
    
    return HttpResponse( json.dumps(to_dict(result)) )


@login_required
@require_GET
def user_view(request):
    if not request.user.is_staff:
        raise PermissionDenied
    
    users_list = User.objects.all()
    dict_list = [to_dict(x) for x in users_list]
    for d, u in zip(dict_list, users_list):
        d['sensors'] = [to_dict(x) for x in u.sensor_set.all().distinct()]
        #print u, '-- ', u.sensor_set.all()
    return HttpResponse(json.dumps(dict_list))



