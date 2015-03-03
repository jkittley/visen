#encoding:UTF-8
import datetime
from sd_store.models import Sensor, Channel, SensorReading
from frontend.models import Sensor_profile, Chart

def default(request):

    return_obj = {}
    return_obj['default_data'] = {}
    return_obj['default_data']['sensor_profiles']  = Sensor_profile.objects.all().order_by('longname')
    return_obj['default_data']['channels'] = Channel.objects.all().order_by('name')
    # return_obj['default_data']['charts']   = Chart.objects.all().order_by('name')

    return_obj['default_data']['months']   = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    return_obj['default_data']['years']    = range(2013,1+datetime.datetime.now().year)
    
    return return_obj

