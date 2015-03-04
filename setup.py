"""install"""
import os
from setuptools import setup, find_packages
import datetime

NOW = datetime.datetime.now()
MAJOR = 0

def read(fname):
    """README helper fuction"""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="solpy",
    version="%s.%s.%s.%s" % (MAJOR, NOW.month + 12, NOW.day, NOW.hour),
    author="Nathan Charles",
    author_email="ncharles@gmail.com",
    description=("Solar Performance and Design library"),
    license="LGPL",
    keywords="solar pv",
    url="https://github.com/nrcharles/solpy",
    packages=find_packages(),
    long_description=read('README.rst'),
    install_requires=['geopy', 'numpy', 'matplotlib', 'scipy', 'pyephem', \
            'caelum', 'mock'],
    package_data={'': ['*.json', '*.csv', 'pvcli' '*.rst']},
    test_suite='tests.unit',
    classifiers=[
        "Development Status :: 4 - Beta",
        ("License :: OSI Approved ::" \
            " GNU Library or Lesser General Public License (LGPL)"),
    ],
)
