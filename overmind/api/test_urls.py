from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from api.provisioning import ProviderHandler, NodeHandler, ImageHandler
import api
from urls import CsrfExemptResource


# The test url creates resources that do not require authentication
api.provisioning._TESTING = True

provider_resource = CsrfExemptResource(ProviderHandler)
image_resource = CsrfExemptResource(ImageHandler)
node_resource = CsrfExemptResource(NodeHandler)

urlpatterns = patterns('',
    url(r'^providers/(?P<provider_id>\d+)/images/$', image_resource),
    url(r'^providers/(?P<provider_id>\d+)/images/(?P<id>\d+)$', image_resource),
    url(r'^providers/$', provider_resource),
    url(r'^providers/(?P<id>\d+)$', provider_resource),
    url(r'^nodes/$', node_resource),
    url(r'^nodes/(?P<id>\d+)$', node_resource),
)
