from datetime import timedelta
# List of modules to import when celery starts.
CELERY_IMPORTS = ("tasks", )

CELERY_CACHE_BACKEND = "dummy"

## Result store settings.
#CELERY_RESULT_BACKEND = "database"
#CELERY_RESULT_DBURI = "sqlite:///mydatabase.db"

## Broker settings.
BROKER_TRANSPORT = "sqlalchemy"
BROKER_HOST = "sqlite:///celerydb.sqlite"


## Worker settings
## If you're doing mostly I/O you can have more processes,
## but if mostly spending CPU, try to keep it close to the
## number of CPUs on your machine. If not set, the number of CPUs/cores
## available will be used.
CELERYD_CONCURRENCY = 2

CELERYBEAT_SCHEDULE = {
    "query_printjobs": {
        "task": "tasks.get_qr_queue",
        "schedule": timedelta(seconds=10),
    },
    "query_printers": {
        "task": "tasks.get_printers",
        "schedule": timedelta(hours=24),
    },
    "printer_heartbeat": {
        "task": "tasks.get_printer_heartbeat",
        "schedule": timedelta(hours=24),
    },
}

try:
    from local_config import *
except:
    pass
