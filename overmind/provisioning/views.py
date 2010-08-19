from django.shortcuts import render_to_response
from overmind.provisioning.models import Provider, Instance


def nodes(request):
    provider_list = Provider.objects.all()
    instance_list = Instance.objects.all()
    return render_to_response('overview.html', {
        'instance_list': instance_list,
        'provider_list': provider_list,
    })
