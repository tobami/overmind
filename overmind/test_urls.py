from django.conf.urls.defaults import patterns, include
from urls import urlpatterns as normal_urlpatterns

urlpatterns = patterns('',
    (r'^api/', include('overmind.api.test_urls'))
)

urlpatterns += normal_urlpatterns
