import json

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.app.wsgi import ControllerBase, Response, route, WSGIApplication

simple_switch_instance_name = 'my_rest_api_app'
switches_url = '/simpleswitch/switches'

class MyRestApp(simple_switch_13.SimpleSwitch13):

  _CONTEXTS = {'wsgi': WSGIApplication}

  def __init__(self, *args, **kwargs):
    super(MyRestApp, self).__init__(*args, **kwargs)
    
    # keep track of connected switches by their ID
    self.switches = {}
    
    wsgi = kwargs['wsgi']
    wsgi.register(MyController, 
                  {simple_switch_instance_name: self})

  # called when a switch connects or disconnects
  # MAIN_DISPATCHER: switch finished OpenFlow handshake; ready
  # DEAD_DISPATCHER: switch disconnected; remove it
  @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
  def _state_change_handler(self, event):
    datapath = event.datapath
    if event.state == MAIN_DISPATCHER:
      # switch just connected, add it to dictionary
      self.switches[datapath.id] = datapath
    elif event.state == DEAD_DISPATCHER:
      # switch just disconnected, remove it from dictionary
      if datapath.id in self.switches:
        del self.switches[datapath.id]

class MyController(ControllerBase):
  
  def __init__(self, req, link, data, **config):
    super().__init__(req, link, data, **config)
    self.app = data[simple_switch_instance_name]

  # handle GET requests to /simpleswitch/switches
  @route('simpleswitch', switches_url, methods=['GET'])
  # no dpid requirement needed since we're getting all switches
  def get_switches(self, req, **kwargs):
    # Get all switch IDs and return them as a JSON list
    dpids = list(self.app.switches.keys())
    body = json.dumps(dpids)
    return Response(content_type='application/json', text=body)
