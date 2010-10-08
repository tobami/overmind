from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.conf import settings


urlpatterns = []

if settings.DEBUG:
    urlpatterns = patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

from django.contrib import admin
admin.autodiscover()

# Admin interface
urlpatterns += patterns('', (r'^admin/(.*)', admin.site.root),)

urlpatterns += patterns('',
    (r'^api/', include('overmind.api.urls')),
    
    (r'^overview/$', 'provisioning.views.overview'),
    (r'^provider/$', 'provisioning.views.provider'),
    (r'^node/$', 'provisioning.views.node'),
    (r'^settings/$', 'provisioning.views.settings'),
    
    # Create
    (r'^provider/new/$', 'provisioning.views.newprovider'),
    (r'^node/new/$', 'provisioning.views.newnode'),
    # Update
    (r'^provider/update/$',\
        'provisioning.views.updateproviders'),
    # Reset
    (r'^node/(?P<node_id>\d+)/reboot/$', 'provisioning.views.rebootnode'),
    # Delete
    (r'^provider/(?P<provider_id>\d+)/delete/$',\
        'provisioning.views.deleteprovider'),
    (r'^node/(?P<node_id>\d+)/destroy/$',\
        'provisioning.views.destroynode'),
    #(r'^$', 'redirect_to', {'url': '/overview/'}),
    
    # Users
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^accounts/new/$', 'provisioning.views.adduser'),
    (r'^accounts/edit/(?P<id>\d+)/$', 'provisioning.views.edituser'),
    (r'^accounts/delete/(?P<id>\d+)/$', 'provisioning.views.deleteuser'),
)
