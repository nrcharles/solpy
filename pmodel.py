"""celery worker"""
from celery import Celery
import pv
import os

HOSTNAME = os.getenv("BROKERHOST")

if not HOSTNAME:
    print "Defaulting to localhost"
    HOSTNAME = 'localhost'

APP = Celery('pmodel', backend='amqp', broker='amqp://guest@%s//' % HOSTNAME)

APP.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

@APP.task
def model_plant(json_def):
    """model sub task"""
    plant = pv.json_system(json_def)
    yearone = plant.model(single_thread=True)
    p_dc = sum([i.array.output(1000) for i in plant.shape])
    plant_dict = plant.dump()
    plant_dict['yearone'] = yearone.annual_output
    plant_dict['DCnominal'] = int(p_dc)
    return plant_dict

#celery -A pmodel worker --loglevel=info  -n worker1.%h
#--autoscale=10,4 --autoreload
