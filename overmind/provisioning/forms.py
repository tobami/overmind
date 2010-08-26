from django import forms
from django.forms import ModelForm
from overmind.provisioning.models import Provider, Instance

class ProviderForm(ModelForm):
    class Meta:
        model = Provider


class GenericInstanceForm(ModelForm):
    class Meta:
        model  = Instance
        fields = ('name', 'provider')


class InstanceForm(GenericInstanceForm):
    #TODO: Choices should be dynamically created depending on the chosen provider
    DUMMY_CHOICES = (('TODO', 'TODO'),)
    flavor        = forms.CharField(max_length=10,
        widget=forms.Select(choices=DUMMY_CHOICES))
    image         = forms.CharField(max_length=20,
        widget=forms.Select(choices=DUMMY_CHOICES))
    realm        = forms.CharField(max_length=10,
        widget=forms.Select(choices=DUMMY_CHOICES))
