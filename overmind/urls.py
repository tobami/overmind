from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.conf import settings


urlpatterns = []

if settings.DEBUG:
    urlpatterns = patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

urlpatterns += patterns('',
    (r'^api/', include('overmind.api.urls')),
    
    (r'^overview/$', 'overmind.provisioning.views.overview'),
    (r'^provider/$', 'overmind.provisioning.views.provider'),
    (r'^node/$', 'overmind.provisioning.views.node'),
    
    # Create
    (r'^provider/new/$', 'overmind.provisioning.views.newprovider'),
    (r'^node/new/$', 'overmind.provisioning.views.newnode'),
    # Update
    (r'^provider/update/$',\
        'overmind.provisioning.views.updateproviders'),
    # Reset
    (r'^node/(?P<node_id>\d+)/reboot/$', 'overmind.provisioning.views.rebootnode'),
    # Delete
    (r'^provider/(?P<provider_id>\d+)/delete/$',\
        'overmind.provisioning.views.deleteprovider'),
    (r'^node/(?P<node_id>\d+)/destroy/$',\
        'overmind.provisioning.views.destroynode'),
    #(r'^', 'redirect_to', {'url': '/overview/'}),
)
