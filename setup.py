import os
from setuptools import setup,find_packages
import datetime
"""setup.py and README must be copied to parent directory in order to build
a valid setuptools package"""

NOW = datetime.datetime.now()
MAJOR = 0

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "solpy",
    version = "%s.%s.%s.%s" % (MAJOR, NOW.month, NOW.day, NOW.hour),
    author = "Nathan Charles",
    author_email = "ncharles@gmail.com",
    description = ("Solar Performance and Design library"),
    license = "LGPL",
    keywords = "solar pv",
    url = "https://github.com/nrcharles/solpy",
    packages=find_packages(),
    long_description=read('README'),
    install_requires = ['geopy','numpy','matplotlib','scipy','pyephem'],
    package_data={'': ['*.json','*.csv','pvcli']},
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    ],
)
