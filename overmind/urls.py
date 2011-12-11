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
)

# Provisioning
urlpatterns += patterns('',
    (r'^overview/$', 'provisioning.views.overview'),
    (r'^provider/$', 'provisioning.views.provider'),
    (r'^node/$', 'provisioning.views.node'),
    (r'^settings/$', 'provisioning.views.settings'),
    
    # Create
    (r'^provider/new/$', 'provisioning.views.newprovider'),
    (r'^node/new/$', 'provisioning.views.newnode'),
    (r'^node/image/add/$', 'provisioning.views.addimage'),
    (r'^node/image/(?P<image_id>\d+)/remove/$', 'provisioning.views.removeimage'),
    
    # Update
    (r'^provider/update/$', 'provisioning.views.updateproviders'),
    
    # Reboot
    (r'^node/(?P<node_id>\d+)/reboot/$', 'provisioning.views.rebootnode'),
    
    # Delete
    (r'^provider/(?P<provider_id>\d+)/delete/$',\
        'provisioning.views.deleteprovider'),
    (r'^node/(?P<node_id>\d+)/destroy/$', 'provisioning.views.destroynode'),

    (r'^$', redirect_to, {'url': '/overview/', 'permanent': False}),
)

# Users
urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^accounts/new/$', 'provisioning.views.adduser'),
    (r'^accounts/edit/(?P<id>\d+)/$', 'provisioning.views.edituser'),
    (r'^accounts/delete/(?P<id>\d+)/$', 'provisioning.views.deleteuser'),
)
