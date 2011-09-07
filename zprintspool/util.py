from datetime import datetime
from restkit import Resource
import isodate
import simplejson


def get_label_queues(host='https://mepimoz.dimagi.com/api/zebra_queue?format=json'):
    res = Resource('http://localhost:8000')
    auth_params = {'username':'dmyung', 'api_key': 'fooooo'}
    r = res.get('/api/zebra_queue/',  params_dict=auth_params)

    json = simplejson.loads(r.body_string())


    for instance in json['objects']:
        uri = instance['resource_uri']
        zpl_code= instance['zpl_code']
        instance['fulfilled_date'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000")
        res.put(uri, simplejson.dumps(instance), headers={'Content-Type': 'application/json'}, params_dict=auth_params)

        print "printing!"
        print zpl_code


if __name__ == "__main__":
    get_label_queues()

