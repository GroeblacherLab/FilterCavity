''' 
BSD 3-Clause License

Copyright (c) 2021, GroeblacherLab
All rights reserved.

Code necesary to run the server with Pyro.

Developed mainly by B.J.Hensen

'''

import logging
import Pyro4
import threading
import Pyro4.naming
import Pyro4.errors
Pyro4.config.DETAILED_TRACEBACK = True
#only basic object (as class, lists...) can be serialised and passed trough Pyro, using other serialisation allows to pass also other objects (like np.array, ...)
#Pyro4.config.SERIALIZER = 'pickle'
#Pyro4.config.SERIALIZERS_ACCEPTED=set(['serpent','json','marshal','pickle'])
Pyro4.config.SERVERTYPE = "multiplex"

def _start_threaded_nameserver(host):
    target = lambda:Pyro4.naming.startNSloop(host=host)
    ns_thread = threading.Thread(target=target).start()
    ns = Pyro4.locateNS(host=host)
    return ns, ns_thread

def find_or_start_nameserver(host):
    try:
        ns = Pyro4.locateNS(host=host)
        logging.info('Found running nameserver')
    except Pyro4.errors.NamingError:
        ns,_=_start_threaded_nameserver(host)
        logging.info('Created new nameserver')
    return ns
    
def register_on_nameserver(host,share_name,uri, existing_name_behaviour='replace'):
    '''
    register a server on the host with a certain share_name, the existing_name_behaviour determines if the server name is replaced or incremented in number

    example of usage:
        host = '192.168.1.XXX' 
        nameserver  = True
        share_name  = 'server_first_try'

        daemon = Pyro4.Daemon(host=host, port=9092)
        uri = daemon.register(class_to_expose)

        if nameserver:
            pyro_tools.register_on_nameserver(host, share_name, uri)
    '''
    ns = find_or_start_nameserver(host)
    try:
        ns.lookup(share_name)
        logging.debug(f'share_name {share_name} exists on nameserver')
        if existing_name_behaviour=='replace':
            pass
        elif existing_name_behaviour=='auto_increment':
            share_name_split = share_name.split('_')
            if len(share_name_split) > 1 and share_name_split[-2] == 'copy':
                share_name_split[-1] = str(int(share_name_split[-1])+1)
                new_share_name = '_'.join(share_name_split)
            else:
                new_share_name = share_name + '_copy_1'
            register_on_nameserver(host,new_share_name,uri,existing_name_behaviour)
            return
        elif existing_name_behaviour=='error':
            raise Exception(f'share name {share_name} already exists on host {host}')
        else:
            raise ValueError('Unknown existing_name_behaviour argument, must be one of replace, auto_increment or error')
        
    except Pyro4.errors.NamingError:
        pass
        
    ns.register(share_name,uri)
    logging.debug(f'registerd {share_name} on nameserver running on host {host}')