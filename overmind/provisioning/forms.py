from django import forms
from django.forms import ModelForm
from overmind.provisioning.models import Provider, Node
from overmind.provisioning.provider_meta import PROVIDERS

class ProviderForm(ModelForm):
    def __init__(self, provider_type, *args, **kwargs):
        super(ProviderForm, self).__init__(*args, **kwargs)
        self.fields['provider_type'].widget = forms.HiddenInput()
        self.fields['provider_type'].initial = provider_type

        for field in ['access_key', 'secret_key']:
            label = PROVIDERS[provider_type].get(field)
            if label is None:
                self.fields[field].widget = forms.HiddenInput()
            else:
                self.fields[field].required = True
                self.fields[field].label = label
                if field == 'secret_key':
                    self.fields['secret_key'].widget = forms.PasswordInput()
        
    class Meta:
        model = Provider
        fields = ('name', 'provider_type', 'access_key', 'secret_key')


class NodeForm(ModelForm):
    provider = forms.ModelChoiceField(
        queryset = Provider.objects.all(),
        widget   = forms.HiddenInput,
    )
    
    def __init__(self, provider, *args, **kwargs):
        super(NodeForm, self).__init__(*args, **kwargs)
        p = Provider.objects.get(id=provider)
        self.fields['provider'].initial = p.id
        
        if PROVIDERS[p.provider_type].get('plugin'):
            for field in PROVIDERS[p.provider_type].get('form_fields', []):
                self.fields[field] = forms.CharField(max_length=30)
        else:
            self.fields['realm'] = forms.ChoiceField()
            for realm in p.get_realms():
                self.fields['realm'].choices += [
                    (realm.id, realm.country + " - " + realm.name)
                ]
            
            self.fields['flavor'] = forms.ChoiceField()
            for flavor in p.get_flavors():
                self.fields['flavor'].choices += [(flavor.id, flavor.name)]
                
            self.fields['image'] = forms.ChoiceField()
            for img in p.get_images():
                self.fields['image'].choices += [(img.id, img.name)]
    
    class Meta:
        model  = Node
        fields = ('provider', 'name')
