# coding=utf-8
import os
import tmy3
import re
#path to epw data
#default = ~/epw/
path = os.environ['HOME'] + "/epw/"

def basename(USAF):
    files = os.listdir(path)
    for f in files:
        if f.find(USAF) is not -1:
            return f[0:f.rfind('.')]


def twopercent(USAF):
    #(DB=>MWB) 2%, MaxDB=
    try:
        fin = open('%s/%s.ddy' % (path,basename(USAF)))
        for line in fin:
            m = re.search('2%, MaxDB=(\d+\.\d*)',line)
            if m:
                return float(m.groups()[0])
    except:
        pass
def ftwopercent(USAF):
    #(DB=>MWB) 2%, MaxDB=
    try:
        fin = open('%s/%s.stat' % (path,basename(USAF)))
        flag = 0
        data = []
        for line in fin:
            if line.find('2%') is not -1:
                flag = 3
            if flag > 0:
                data.append(line.split('\t'))
                flag -= 1
        return float(data[2][5].strip())
    except:
        pass

def fminimum(USAF):
    fin = open('%s/%s.stat' % (path,basename(USAF)))
    for line in fin:
        if line.find('Minimum Dry Bulb') is not -1:
            return float(line[37:-1].split('\xb0')[0])
def minimum(USAF):
    #(DB=>MWB) 2%, MaxDB=
    try:
        fin = open('%s/%s.ddy' % (path,basename(USAF)))
        for line in fin:
            m = re.search('Max Drybulb=(-?\d+\.\d*)',line)
            if m:
                return float(m.groups()[0])
    except:
        pass


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Model a PV system. Currently displays annual output and graph')
    #import sys
    #opts, args = getopt.getopt(sys.argv[1:], 'f:h')
    parser.add_argument('-z', '--zipcode',type=int,required=True)
    args = vars(parser.parse_args())
    #print args

    try:
        #start program
        zip = args['zipcode']

        name, usaf = tmy3.closestUSAF( tmy3.zipToCoordinates(zip))
        print "%s USAF: %s" %  (name, usaf)
        print "Minimum Temperature: %s C" % minimum(usaf)
        print "2%% Max: %s C" % twopercent(usaf)

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except:
        raise
