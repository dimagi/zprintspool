from datetime import datetime
import socket
from restkit import Resource
import isodate
import simplejson
import time
import celeryconfig
from tasks import *
import gevent
from gevent import socket as gsocket




def gsend(host, port, zpl_string, recv=False):
    try:
        s = gsocket.create_connection((host,port), timeout=5)
        s.send(zpl_string)
    except Exception, ex:
        logging.error(repr(ex))
        return False

    if recv:
        try:
            data = ''
            while True:
                #line = fileobj.readline()
                line = s.recv(1024)
                if line is None or len(line) == 0 or line.count('\x03') > 0:
                    break
                data += line
                #print "%s (%d)" % (line.strip(), len(line))
                if not line:
                    logging.error("client disconnected")
                    break
            return data
        except socket.timeout, ex:
            logging.error("GSend Exception: %s, %s" % (ex, ex.__class__))
            return None
    else:
        return True





def do_send(host, port, zpl_string, recv=False): #destination
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((host,port))
        s.send(zpl_string)
    except Exception, ex:
        logging.error("Error trying to establish and send data on socket: %s" % (ex))
        s.close()
        return False


    if recv:
        data = ''
        try:
            while True:
                read = s.recv(1024)
                if read is None or len(read) == 0 or read.count('\x03') > 0:
                    break
                else:
                    data += read

        except Exception, ex:
            logging.error("DoSend Error reading data from socket, %s" % ex)
            return None

        try:
            s.close()
        except Exception, ex:
            logging.error("DoSend Error trying to close socket")
        return data
    else:
        s.close()
        return True
