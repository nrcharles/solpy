import os
from setuptools import setup,find_packages
"""setup.py and README must be copied to parent directory in order to build
a valid setuptools package"""

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "solpy",
    version = "0.2.0",
    author = "Nathan Charles",
    author_email = "ncharles@gmail.com",
    description = ("Solar Performance and Design library"),
    license = "LGPL",
    keywords = "solar pv",
    url = "https://github.com/nrcharles/solpy",
    packages=find_packages(),
    long_description=read('README'),
    install_requires = ['geopy','numpy','matplotlib','scipy'],
    package_data={'': ['*.json','*.csv','data.fdf']},
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    ],
)
