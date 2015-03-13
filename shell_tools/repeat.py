import os

for y in range(2014,2015,1):

    # Non inclusive
    for m in range(10,13, 1):

        path =  'python ../manage.py import_weather'
        path += ' --month '
        path += str(m)
        path += ' --year '
        path += str(y)

        print path

        os.system(path)
