Installation
------------
solpy can be installed via easy_install or pip.  Some of the prereqs can be installed via packagemanagment.

Homebrew on Mac OS X
----------------------
    brew install geos gfortran
    pip install solpy

apt-get on Ubuntu
-------------------
    sudo apt-get install python-geopy python-numpy python-scipy python-matplotlib python-pip
    sudo apt-get install gfortran libatlas-dev liblapack-dev #dev reqs
    sudo pip install solpy

tmy3 data does needs to be downloaded from NREL, currently the default location is ~/tmy3/
[tmy3 dataset]: http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3/tmy3.tar.gz
