#encoding:UTF-8
from django.core.management.base import BaseCommand
#from pricing import wind, grid  

class Command(BaseCommand):
    #args = '<poll_id poll_id ...>'
    help = 'Populates the db for the pricing applications'

    def handle(self, *args, **options):
        pass
        #grid.populate()
        #self.stdout.write('Successfully populated grid pricing information')
        #wind.populate()
        #self.stdout.write('Successfully populated grid pricing information')
    
        self.stdout.write("populating sd_store.. ")
        
        userDataText = """\
        acr@ecs.soton.ac.uk, OliverParson, PHONE_NUM,
        e.costanza@ieee.org, FigureEnergy, +447545024497, 
        ecenergy27@ecs.soton.ac.uk, Password123!, PHONE_NUM, 
        ecenergy30@ecs.soton.ac.uk, Password123!, PHONE_NUM, 
        ecenergy37@ecs.soton.ac.uk, Password123!, PHONE_NUM, 
        ecenergy39@ecs.soton.ac.uk, Password123!, PHONE_NUM,
        """
#        """
#        ecenergy28@ecs.soton.ac.uk, Password123!, control
#        ecenergy32@ecs.soton.ac.uk, Password123!, time_priority
#        ecenergy33@ecs.soton.ac.uk, Password123!, price_priority
#        ecenergy36@ecs.soton.ac.uk, Password123!, 
#        """
        
        userData = []
        lines = iter( userDataText.split("\n") )
        for line in lines:
            if len(line) < 8:
                continue
            try:
                info = line.split(',')
                info = [x.strip().rstrip() for x in info]
                if len(info) == 4:
                    userData.append(info)
            except StopIteration:
                pass
        
        from ... import populatedb 
        
        import os
        icons_path = os.path.join(os.getcwd(), 'frontend', 'static', 'imgs', 'event_icons')
        #icons_path = os.path.join(icons_path, 'logger')
        icon_filenames = os.listdir(icons_path)
        icon_filenames = filter(lambda x: x.endswith('.png'), icon_filenames)
        icon_filenames = [x for x in icon_filenames if 'always' not in x]
        icon_url = os.path.join('media', 'imgs', 'event_icons')
        logger_icons = [os.path.join(icon_url, 'logger', filename) 
                        for filename in icon_filenames]
        practice_icons = [os.path.join(icon_url, filename) 
                          for filename in icon_filenames]
        
        populatedb.populate(userData, logger_icons, practice_icons)

        self.stdout.write("..done\n")
