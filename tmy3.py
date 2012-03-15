import csv
import datetime
import os

#path to tmy3 data
#default = ~/tmp3/
path = os.environ['HOME'] + "/tmy3/"

def strptime(string):
    Y = int(string[6:8])
    M = int(string[0:2])
    D = int(string[3:5])
    h = int(string[11:13])
    m = int(string[14:16])
    return datetime.datetime(Y, M, D) + datetime.timedelta(hours=h, minutes=m)

class get_data():
    def __init__(self, USAF):
        filename = path + USAF + 'TY.csv'
        self.csvfile = open(filename)
        print self.csvfile.readline()
        self.tmy_data = csv.DictReader(self.csvfile)
    def __iter__(self):
        return self
    def next(self):
        i = self.tmy_data.next()
        #['Date (MM/DD/YYYY)', 'Time (HH:MM)'
        sd = i['Date (MM/DD/YYYY)'] +' '+ i['Time (HH:MM)']
        dni = i['DNI (W/m^2)']
        d = strptime(sd)
        return d, dni
    def __del__(self):
        self.csvfile.close()

def find_close(latitude,longitude):
    import math
    index = open(path + 'TMY3_StationsMeta.csv')
    index_data = csv.DictReader(index)
    d1 = 9999
    name = ''
    usaf = ''
    for i in index_data:
        d2 = math.sqrt(math.pow((float(i['Latitude']) - latitude),2) +math.pow((float(i['Longitude']) - longitude),2))
        if d2 < d1:
            d1 = d2
            name = i['Site Name']
            usaf = i['USAF']
    return name, usaf

if __name__ == "__main__":
    name, usaf = find_close(40,-76)
    for d,dni in get_data(usaf):
        print dni
