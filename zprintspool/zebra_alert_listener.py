import simplejson
from gevent.server import StreamServer
import logging
import tasks
from datetime import datetime


#do get printers from server via rest
#cache printers and their IPs
#when receiving event, then lookup then set data strucutre and push over

#received ERROR CONDITION: HEAD OPEN [ZBR3913909] :: ('192.168.0.85', 3971)
#received ALERT: PRINTER PAUSED [ZBR3913909] :: ('192.168.0.85', 3972)
#received ERROR CLEARED: HEAD OPEN [ZBR3913909] :: ('192.168.0.85', 3973)
#received ALERT CLEARED: PRINTER PAUSED [ZBR3913909] :: ('192.168.0.85', 3974)
import celeryconfig
from restkit import Resource

def identify_printer(address,printers):
    for k,v in printers.items():
        if address[0] == v['ip_address']:
            return v['resource_uri']
    return None

printers= {}

def zebra_alert_handler(socket, address):
    try:
        fileobj = socket.makefile()

        while True:
            line = fileobj.readline()
            if not line:
                break
            fileobj.write(line)
            fileobj.flush()
            raw_msg = line.strip()
            message_split = raw_msg.split(':')
            if message_split[0] == 'ALERT' or message_split[0] == 'ERROR CONDITION':
                #it's an alert/error,
                is_cleared=False
            elif message_split[0] == 'ALERT CLEARED' or message_split[0] == 'ERROR CLEARED':
                is_cleared=True
            else:
                is_cleared=True
            condition = message_split[1].split('[')[0].strip().lower()


            printer_uri = identify_printer(address, printers)

            host='http://localhost:8000'
            res = Resource(host)
            auth_params = {'username':celeryconfig.ZPRINTER_USERNAME, 'api_key': celeryconfig.ZPRINTER_API_KEY}
            #r = res.get('/api/zebra_status/',  params_dict=auth_params)
            new_instance = {}
            new_instance['printer'] = printer_uri
            new_instance['event_date'] =  datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000")
            new_instance['status'] = condition
            new_instance['is_cleared'] = is_cleared

            res.post('api/zebra_status/', simplejson.dumps(new_instance), headers={'Content-Type': 'application/json'}, params_dict=auth_params)


            print "Condition: %s: %s" % (condition, is_cleared)

    except Exception, ex:
        logging.error("Unknown exception, gobbling up: %s", ex)


printers = tasks.get_printers()
server = StreamServer(('0.0.0.0',9111), zebra_alert_handler) # creates a new server
server.serve_forever() # start accepting new connections
