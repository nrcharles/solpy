from celery import Celery
import pv
import os

hostname = os.getenv("BROKERHOST")

if not hostname:
    print "Defaulting to localhost"
    hostname = 'localhost'

app = Celery('pmodel', backend='amqp', broker='amqp://guest@%s//' % hostname)

app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

@app.task
def modelPlant(jsonDef):
    plant = pv.jsonToSystem(jsonDef)
    yearone = plant.model(singleThread = True)
    PDC = sum([i.array.output(1000) for i in plant.shape])
    plantDict = plant.dump()
    plantDict['yearone'] = yearone.annualOutput
    plantDict['DCnominal'] = int(PDC)
    return plantDict

#celery -A pmodel worker --loglevel=info  -n worker2.%h  --autoscale=10,4 --autoreload
