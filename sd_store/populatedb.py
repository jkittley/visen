#encoding:UTF-8
'''
Created on 18 Jan 2012

@author: enrico
'''
import os
from datetime import datetime#, timedelta

from django.contrib.auth.models import Group, Permission, User
#from django.core.files import File 

from sd_store.models import UserProfile, SensorReading, MeteringPoint, \
                   Meter, Event, EventType, StudyInfo

def delete_all():
    User.objects.all().delete()
    UserProfile.objects.all().delete()
    Group.objects.all().delete()
    Permission.objects.all().delete()
    
    Meter.objects.all().delete()
    SensorReading.objects.all().delete()
    MeteringPoint.objects.all().delete()
    
    Event.objects.all().delete()
    EventType.objects.all().delete()

def populate_event_types(logger_icons, practice_icons):
    
    for (logger_icon, practice_icon) in zip(logger_icons, practice_icons):
        name = os.path.basename(logger_icon)
        name = name.replace('_',' ').replace('.png', '')
        eventType = EventType(
            name = name,
            icon = logger_icon,
            alt_icon = practice_icon
        )
        eventType.save()

def populate(userData, logger_icons, practice_icons):
    # userData is a list of tuples containing
    # (username, email, password, alertmePassword)
    
    #delete_all()
    
    superUser = User(username = "superuser", is_superuser = True, is_staff = True)
    superUser.set_password('F1gur3!')
    try:
        superUser.save()
    except:
        pass
    
    controlGroup = Group(name = 'control')
    try:
        controlGroup.save()
    except:
        pass
    
    populate_event_types(logger_icons, practice_icons)
    
    for (username, password, phone_num, groups_string) in userData:
        groups = groups_string.split(' ')
        groups = [g for g in groups if len(g) > 0]
        
        user, _ = User.objects.get_or_create(username=username)
        # TODO: the password does not seem to work correctly if it is not set via set_password
        user.set_password(password)
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user, phone_number=phone_num)
        profile.save()

        # create a group for this user, anyone in this group can access the data?
        userGroup, created = Group.objects.get_or_create(name=user.id)
        if created:
            userGroup.save()
        user.groups.add(userGroup)
        
        for group_name in groups:
            g, created = Group.objects.get_or_create(name=group_name)
            if created:
                g.save()
            user.groups.add(g)
        user.save()
        
        si, _ = StudyInfo.objects.get_or_create(
          user = user,
          baseline_consumption = 4.0,
          start_date = datetime(2012, 6, 10, 0, 0, 0),
          initial_credit = 50.0
        )
        si.save()
        
if __name__ == '__main__':
    pass

