from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
import api
from api.handlers import ProviderHandler, NodeHandler

# The test url creates resources that do not require authentication
api.handlers._TESTING = True

class CsrfExemptResource(Resource):
    '''Django 1.2 CSRF protection can interfere'''
    def __init__(self, handler, authentication = None):
        super(CsrfExemptResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

provider_resource = CsrfExemptResource(ProviderHandler)
node_resource = CsrfExemptResource(NodeHandler)

urlpatterns = patterns('',
    url(r'^providers/$', provider_resource),
    url(r'^providers/(?P<id>\d+)$', provider_resource),
    url(r'^nodes/$', node_resource),
    url(r'^nodes/(?P<id>\d+)$', node_resource),
)
