import simplejson
from datetime import datetime
from celery.decorators import periodic_task
from celery.schedules import crontab
from celery.decorators import task
from restkit import Resource
import logging
from util import do_send,gsend

import celeryconfig


printer_dict = {}

is_bootstrapped=False

def bootstrap():
    """
    Bootstrap all printers known to the system.
    Get printers
    Set the alerts to go to this host
    """
    get_printers()
    set_alert_destination()

#@periodic_task(run_every=crontab(hour=23, minute=59))
@task
def get_printers(host=celeryconfig.SERVER_HOST):
    res = Resource(host)
    auth_params = {'username':celeryconfig.ZPRINTER_USERNAME, 'api_key': celeryconfig.ZPRINTER_API_KEY}
    r = res.get('/api/zebra_printers/',  params_dict=auth_params)
    json = simplejson.loads(r.body_string())
    #load printers into memory, yo for caching purposes

    for printer in json['objects']:
        printer_uri = printer['resource_uri']
        printer_dict[printer_uri]=printer
    return printer_dict

@task
def set_alert_destination():
    """Set the printer alert endpoing to this host's listening port
    """
    listener_ip_address = celeryconfig.ZPRINT_PROXY
    #listener_ip_address = '192.168.10.20' # actual setup

    listener_port = 9111
    if len(printer_dict.keys()) == 0:
        get_printers()
    alert_text="""
    ^XA
    ^SX*,D,Y,Y,%s,9111
    ^XZ
    """ % (listener_ip_address)
    for k,v in printer_dict:
        host = v['ip_address']
        port = v['port']
        do_send(host, port, alert_text)

@task
def get_printer_heartbeat(host=celeryconfig.SERVER_HOST):
    """
    Task to actively monitor the printer's status (vs. waiting to get alerts)
    """
    if len(printer_dict.keys()) == 0:
        get_printers()
    msg_text = """^XA^HH^XZ"""
    for k,v in printer_dict.items():
        host = v['ip_address']
        port = v['port']
        printer_uri = v['resource_uri']

        info = gsend(host, port, msg_text, recv=True)

        #prepare the rest resource for sending info to server
        res = Resource(host)
        auth_params = {'username':celeryconfig.ZPRINTER_USERNAME, 'api_key': celeryconfig.ZPRINTER_API_KEY}

        new_instance = dict()
        new_instance['printer'] = printer_uri
        new_instance['event_date'] =  datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000")
        new_instance['status'] = 'printer uptime heartbeat'

        if info is None or info == False:
            #failed to reach printer or receive data
            new_instance['is_cleared'] = False
        elif isinstance(info, str):
            #it's a string with info
            if info.count('ZPL MODE') > 0:
                #we got diagnostic info from printer
                new_instance['is_cleared'] = True
            else:
                #something else, error
                new_instance['is_cleared'] = False

        res.post('api/zebra_status/', simplejson.dumps(new_instance), headers={'Content-Type': 'application/json'}, params_dict=auth_params)

@task
def get_qr_queue(host=celeryconfig.SERVER_HOST):

    if not is_bootstrapped:
        bootstrap()

    res = Resource(host)
    auth_params = {'username':celeryconfig.ZPRINTER_USERNAME, 'api_key': celeryconfig.ZPRINTER_API_KEY}
    r = res.get('/api/zebra_queue/',  params_dict=auth_params)
    json = simplejson.loads(r.body_string())

    if len(printer_dict.keys()) == 0:
        get_printers()

    if len(json['objects']) > 0:
        for instance in json['objects']:
            uri = instance['resource_uri']
            zpl_code= instance['zpl_code']

            printer_uri = instance['destination_printer']
            printer_ip = printer_dict[printer_uri]['ip_address']
            printer_port = printer_dict[printer_uri]['port']

            instance['fulfilled_date'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000")
            res.put(uri, simplejson.dumps(instance), headers={'Content-Type': 'application/json'}, params_dict=auth_params)
            do_send(printer_ip, printer_port, zpl_code, recv=False)
    else:
        logging.debug("no jobs")
