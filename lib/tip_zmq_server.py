
import time
import threading
import logging
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator

from lib.tip_config import config, internal
from lib.tip_srv_lib import parse_request

def serve_requests ():
    context = zmq.Context()
    # save context for further usage to internal state dict
    internal['zmq_context'] = context
    # FIXME: authentication is not working in the moment
    auth = ThreadAuthenticator(context,log=logging.getLogger())
    auth.start()
    auth.allow('127.0.0.1')
    auth.allow('localhost')
    
    set_allowed_IPs(auth)

    socket = context.socket(zmq.REP)
    socket.zap_domain = b'global'
    bind_str = "tcp://*:"+str(config['system'].get('zmq_port',5000))
    logging.info("TIP serving via ZMQ %s" % bind_str)
    socket.bind(bind_str)

    while True:
        #  Wait for next request from client
        message = socket.recv_string()
        logging.debug("Received request: %s" % message)
        #  Send reply back to client:
        #  everything is handled by the tip_srv_lib parse_request
        socket.send_string(str(parse_request(message)))
    
    #auth.stop()

def srv_thread():
    thread = threading.Thread( target = serve_requests, args = () )
    thread.start()

def set_allowed_IPs(auth):
    for IP in str(config['system'].get('allowed_ips',"")).split(" "):
        logging.info("Add " + IP + " to allowed IP list.")
        auth.allow(IP)
    
    
    


if __name__ == "__main__":
    from lib.tip_config import config, load_config, convert_to_dict
    config = convert_to_dict(load_config())
    #serve_requests()
    srv_thread()
    time.sleep(10)