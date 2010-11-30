from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from api.provisioning import ProviderHandler, NodeHandler, ImageHandler


auth = HttpBasicAuthentication(realm="overmind")
ad = { 'authentication': auth }

class CsrfExemptResource(Resource):
    '''Django 1.2 CSRF protection can interfere'''
    def __init__(self, handler, authentication = None):
        super(CsrfExemptResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

provider_resource = CsrfExemptResource(ProviderHandler, **ad)
image_resource = CsrfExemptResource(ImageHandler, **ad)
node_resource = CsrfExemptResource(NodeHandler, **ad)

urlpatterns = patterns('',
    url(r'^providers/(?P<provider_id>\d+)/images/$', image_resource),
    url(r'^providers/(?P<provider_id>\d+)/images/(?P<id>\d+)$', image_resource),
    url(r'^providers/$', provider_resource),
    url(r'^providers/(?P<id>\d+)$', provider_resource),
    url(r'^nodes/$', node_resource),
    url(r'^nodes/(?P<id>\d+)$', node_resource),
)
