from django import forms
from django.forms import ModelForm
from overmind.provisioning.models import Provider, Instance, PROVIDER_META

class ProviderForm(ModelForm):
    def __init__(self, provider_type, *args, **kwargs):
        super(ProviderForm, self).__init__(*args, **kwargs)
        self.fields['provider_type'].widget = forms.HiddenInput()
        self.fields['provider_type'].initial = provider_type
        self.fields['access_key'].label = PROVIDER_META[provider_type]['access_key']
        self.fields['secret_key'].label = PROVIDER_META[provider_type]['secret_key']
        if PROVIDER_META[provider_type]['secret_key'] is None:
            self.fields['secret_key'].widget = forms.HiddenInput()
    
    class Meta:
        model = Provider


class InstanceForm(ModelForm):
    provider = forms.ModelChoiceField(
        queryset = Provider.objects.all(),
        widget   = forms.HiddenInput,
    )
    realm    = forms.ChoiceField()
    flavor   = forms.ChoiceField()
    image    = forms.ChoiceField()
    
    def __init__(self, provider, *args, **kwargs):
        super(InstanceForm, self).__init__(*args, **kwargs)
        p = Provider.objects.get(id=provider)
        self.fields['provider'].initial = p.id
        self.fields['realm'].choices = [
            (realm.id, realm.country + " - " + realm.name) for realm in p.get_realms()
        ]
        self.fields['image'].choices = [
            (img.id, img.name) for img in p.get_images()
        ]
        self.fields['flavor'].choices = [
            (flavor.id, flavor.name) for flavor in p.get_flavors()
        ]
    
    class Meta:
        model  = Instance
        fields = ('provider', 'name')
