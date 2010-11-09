from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

from provisioning.models import Provider, Node, Image, Location, Size
from provisioning.provider_meta import PROVIDERS

class ProviderForm(forms.ModelForm):
    def __init__(self, provider_type, *args, **kwargs):
        super(ProviderForm, self).__init__(*args, **kwargs)
        self.fields['provider_type'].widget = forms.HiddenInput()
        self.fields['provider_type'].initial = provider_type
        provider_type_info = PROVIDERS.get(provider_type, {})
        
        for field in ['access_key', 'secret_key']:
            label = provider_type_info.get(field)
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


class AddImageForm(forms.Form):
    provider = forms.ModelChoiceField(
        queryset = Provider.objects.all(),
        widget   = forms.HiddenInput,
    )
    image_id = forms.CharField(widget=forms.HiddenInput, required=False)
    favimage1 = forms.CharField(label="Type an image id", required=False)
    favimage2 = forms.ChoiceField(label="Select an image", choices=[])
    
    def __init__(self, provider_id, *args, **kwargs):
        super(AddImageForm, self).__init__(*args, **kwargs)
        prov = Provider.objects.get(id=provider_id)
        self.fields['provider'].initial = prov.id
        self.fields['favimage2'].choices = []
        for img in prov.get_images():
            self.fields['favimage2'].choices += [(img.id, img.name)]
    
    def clean(self):
        cleaned_data = self.cleaned_data
        image = cleaned_data.get('favimage1')
        if image != "":
            try:
                cleaned_data['image'] = Image.objects.get(
                    provider=cleaned_data['provider'],
                    image_id=image
                )
            except Image.DoesNotExist:
                msg = u"Invalid image id"
                self._errors['favimage1'] = self.error_class([msg])
        else:
            cleaned_data['image'] = Image.objects.get(
                    id=cleaned_data.get('favimage2'))
        if cleaned_data['image'].favorite:
            msg = u"This image is already marked as favorite"
            self._errors['favimage1'] = self.error_class([msg])
        return cleaned_data


class NodeForm(forms.ModelForm):
    provider = forms.ModelChoiceField(
        queryset = Provider.objects.all(),
        widget   = forms.HiddenInput,
    )
    
    def __init__(self, provider_id, *args, **kwargs):
        super(NodeForm, self).__init__(*args, **kwargs)
        prov = Provider.objects.get(id=provider_id)
        self.fields['provider'].initial = prov.id
        provider_info = PROVIDERS[prov.provider_type]
        # Add custom plugin fields
        for field in provider_info.get('form_fields', []):
            # These fields will be added later
            if field in ['location', 'size', 'image']:
                continue
            self.fields[field] = forms.CharField(max_length=30)
        
        # Add location field
        if 'location' in provider_info.get('form_fields', []):
            self.fields['location'] = forms.ChoiceField()
            for location in prov.get_locations():
                self.fields['location'].choices += [
                    (location.id, location.country + " - " + location.name)
                ]
        # Add size field
        if 'size' in provider_info.get('form_fields', []):
            self.fields['size'] = forms.ChoiceField()
            for size in prov.get_sizes():
                self.fields['size'].choices += [(size.id, size.name)]
        # Add image field
        if 'image' in provider_info.get('form_fields', []):
            self.fields['image'] = forms.ChoiceField()
            for img in prov.get_fav_images():
                self.fields['image'].choices += [(img.id, img.name)]
    
    def clean_image(self):
        '''Transform image id to a proper object'''
        image = self.cleaned_data.get('image')
        try:
            image = Image.objects.get(id=image)
        except Image.DoesNotExist:
            msg = u"This image id doesn't exist for this provider"
            self._errors['image'] = self.error_class([msg])
        return image
    
    def clean_location(self):
        location = self.cleaned_data.get('location')
        try:
            location = Location.objects.get(id=location)
        except Location.DoesNotExist:
            msg = u"This location id doesn't exist for this provider"
            self._errors['location'] = self.error_class([msg])
        return location
    
    def clean_size(self):
        size = self.cleaned_data.get('size')
        
        try:
            size = Size.objects.get(id=size)
        except Size.DoesNotExist:
            msg = u"This size id doesn't exist for this provider"
            self._errors['size'] = self.error_class([msg])
        return size
    
    class Meta:
        model  = Node
        fields = ('provider', 'name', 'location', 'size', 'image')

class UserCreationFormExtended(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationFormExtended, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['username'].help_text = None
        self.fields['groups'] = forms.ModelChoiceField(
            queryset=Group.objects.all(),
            initial = 2,#id of group "Operator"
            help_text = None,
            required = True,
            label='Role',
        )
        self.fields['password2'].help_text = None
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'groups')
    
    def save(self, commit=True):
        user = super(UserCreationFormExtended, self).save(commit=False)
        if commit:
            user.save()
        user.groups.add(self.cleaned_data["groups"])
        user.save()
        return user

class BasicEditForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput)
    
    def __init__(self, *args, **kwargs):
        super(BasicEditForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        user = super(BasicEditForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        
        if commit:
            user.save()
        
        return user

class UserEditForm(BasicEditForm):
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        help_text=None,
        required=True,
        initial=2,
        label='Role',
    )
    
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        initial_group = kwargs.get('instance').groups.all()
        if len(initial_group):
            self.fields['group'].initial = initial_group[0].id
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'group')
    
    def save(self, commit=True):
        user = super(UserEditForm, self).save(commit=False)
        user.groups.clear()
        user.groups.add(self.cleaned_data["group"])
        if commit:
            user.save()
        
        return user

class ProfileEditForm(BasicEditForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
