from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

urlpatterns += patterns('',
    (r'^overview/$', 'overmind.provisioning.views.overview'),
    (r'^provider/$', 'overmind.provisioning.views.newprovider'),
    (r'^node/$', 'overmind.provisioning.views.newnode'),
    (r'^provider/(?P<provider_id>\d+)/delete/$',\
        'overmind.provisioning.views.deleteprovider'),
    (r'^node/(?P<node_id>\d+)/delete/$',\
        'overmind.provisioning.views.deletenode'),
    #(r'^', 'redirect_to', {'url': '/overview/'}),
)
