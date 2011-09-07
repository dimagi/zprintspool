from celery.tasks import task
import socket
from gevent import socket as gsocket
from gevent import monkey
import gevent
monkey.patch_socket()



def gsend(host, port, zpl_string, recv=False):
    s = gsocket.create_connection((host,port), timeout=5)
    s.send(zpl_string)
    #fileobj = s.makefile()
    #fileobj.write(zpl_string)
    #fileobj.flush()

    if recv:
        try:
            while True:
                #line = fileobj.readline()
                line = s.recv(256)
                print "%s (%d)" % (line.strip(), len(line))
                if not line:
                    print ("client disconnected")
                    break
        except socket.timeout, ex:
            print "Exception: %s, %s" % (ex, ex.__class__)






def do_send(host, port, zpl_string, recv=False): #destination
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((host,port))
        s.send(zpl_string)
    except Exception, ex:
        print "*** Error sending: %s" % (ex)


    if recv:
        try:
            print s.recv(1024)
            pass
        except Exception, ex:
            print "**** Error trying to read from socket %s" % ex

        try:
            s.close()
        except Exception, ex:
            print "*** Error trying to close socket %s" % ex

