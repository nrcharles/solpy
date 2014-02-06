from distutils.core import setup
setup(name='solpy',
      version='0.1',
      url="https://github.com/nrcharles/solpy",
      package_dir={'solpy': ''},
      package_data={'solpy': ['*.json','*.csv','data.fdf']},
      packages=['solpy'],
      )
