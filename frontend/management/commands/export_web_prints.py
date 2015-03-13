#encoding:UTF-8
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from sd_store.models import *
from frontend.models import *
from datetime import datetime, timedelta
from optparse import make_option
import time, os

import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Command(BaseCommand):
    help = 'Plots data from multiple sensors'

    def handle(self, *args, **options):
        
        for chart_ref in ["calendar"]:
            max_count = 100



            firefox = webdriver.Firefox()
            firefox.get("http://127.0.0.1:8000/")
            username = firefox.find_element_by_id("id_username")
            password = firefox.find_element_by_id("id_password")
            username.send_keys('jacob')
            password.send_keys('123')
            element = firefox.find_element_by_id("login_button")
            element.click()

            firefox.get("http://127.0.0.1:8000/")
            firefox.maximize_window()
            
            count = 0 
            # visualisations = Visualisation.objects.all()
            visualisations = Visualisation.objects.filter(group__icontains='calendar')
            for vis in visualisations:

                # Load charts of this type
                if vis.chart.ref == chart_ref:
                    if count >= max_count:
                        print "Limit reached"
                        break

                    # Load page
                    print vis.name
                    firefox.get("http://127.0.0.1:8000/view/"+str(vis.pk))
                    
                    # Wait for page to load
                    try:
                        element = WebDriverWait(firefox, 10).until(
                            EC.presence_of_element_located((By.ID, "loaded_flag"))
                        )
                    except:
                        count += 1
                        print "Failed to load: "+str(vis.pk)+" "+vis.name
                        continue
                    
                    # Create image directory if needed
                    folder = 'zzz_images/'+str(vis.chart.ref)+'/'+str(vis.group)+"/"
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                    
                    # Allow time to render and take screenshot
                    time.sleep(2)
                    filename = str(vis.name)+'.png'
                    firefox.save_screenshot(filename)
                    os.rename(filename, folder+filename)
                    count += 1
                    print "saved"
                    


            firefox.quit();