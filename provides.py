from charms.reactive import RelationBase, scopes, hook, helpers
from charmhelpers.core import hookenv

import socket
import json

class ReverseProxyProvides(RelationBase):
    scope = scopes.UNIT
#    auto_accessors=['config']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hookenv.atexit(lambda: self.remove_state('{relation_name}.triggered'))
        hookenv.atexit(lambda: self.remove_state('{relation_name}.changed'))
        hookenv.atexit(lambda: self.remove_state('{relation_name}.departed'))

    @hook('{provides:reverseproxy}-relation-{joined,changed}')
    def changed(self):
        self.set_state('{relation_name}.triggered')
        if self.config is not None and helpers.data_changed(hookenv.remote_unit(),self.config):
            self.set_state('{relation_name}.changed')

    @hook('{provides:reverseproxy}-relation-{departed}')
    def departed(self):
        self.set_state('{relation_name}.triggered')
        #self.remove_state('{relation_name}.ready') I don't think this is necessary or desired 
        self.set_state('{relation_name}.departed')
        hookenv.log('reverseproxy.departed','INFO')
        # Clear data_changed
        helpers.data_changed(hookenv.remote_unit(),'')

    def configure(self,ports,hostname=None):
        hostname = hostname or socket.getfqdn()
        relation_info = {
            'hostname': hostname,
            'ports': ports
             }
        self.set_remote(**relation_info)
        self.set_state('{relation_name}.ready')

    def set_cfg_status(self,cfg_good,msg=None):
        ''' After receiving a reverse proxy request, the provider should provide a status update
        cfg_good: Boolean value to represnt if the config was valid
        msg: Optional msg to to explain the status 
        '''
        msg = msg or ''
        if cfg_good:
            status = 'passed: '+msg
            hookenv.log(status,'INFO') 
        else:
            status = 'failed: '+msg
            hookenv.log(status,'WARNING') 
        self.set_remote('cfg_status',status)

    @property
    def config(self):
        if self.get_remote('config') is None:
            return None
        return json.loads(self.get_remote('config'))

