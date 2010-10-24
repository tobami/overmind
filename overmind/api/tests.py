from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from provisioning.models import Provider, Node
import simplejson as json


class GETProviderTest(TestCase):
    urls = 'overmind.test_urls'
    
    def setUp(self):
        op = Group.objects.get(name='Operator')
        self.user = User.objects.create_user(
            username='testuser', email='t@t.com', password='test1')
        self.user.groups.add(op)
        self.user.save()
        
        self.path = "/api/providers/"
        self.client = Client()
        
        self.p1 = Provider(name="prov1", provider_type="DUMMY", access_key="keyzz")
        self.p1.save()
        self.p2 = Provider(name="prov2", provider_type="DUMMY", access_key="keyzz2")
        self.p2.save()
        self.p3 = Provider(name="prov3", provider_type="dedicated")
        self.p3.save()
    
    def test_not_authenticated(self):
        '''A non authenticated user should get 401'''
        response = self.client.get(self.path)
        self.assertEquals(response.status_code, 401)
    
    def test_get_all_providers(self):
        """Get all existing providers"""
        #login = self.client.login(
            #username=self.user.username, password=self.user.password)
        #self.assertTrue(login)
        
        response = self.client.get(self.path)
        self.assertEquals(response.status_code, 200)
        content = json.loads(response.content)
        expected = [
            {'id': self.p1.id, 'access_key': self.p1.access_key,
            'provider_type': self.p1.provider_type, 'name': self.p1.name},
            {'id': self.p2.id, 'access_key': self.p2.access_key,
            'provider_type': self.p2.provider_type, 'name': self.p2.name},
            {'id': self.p3.id, 'access_key': self.p3.access_key,
            'provider_type': self.p3.provider_type, 'name': self.p3.name},
        ]
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_providers_by_type_dummy(self):
        '''Get all providers of type DUMMY'''
        response = self.client.get(self.path + "?provider_type=DUMMY")
        content = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        expected = [
            {'id': self.p1.id, 'access_key': self.p1.access_key,
            'provider_type': self.p1.provider_type, 'name': self.p1.name},
            {'id': self.p2.id, 'access_key': self.p2.access_key,
            'provider_type': self.p2.provider_type, 'name': self.p2.name},
        ]
        self.assertEquals(json.loads(response.content), expected)

    def test_get_providers_by_type_dedicated(self):
        '''Get all providers of type dedicated'''
        response = self.client.get(self.path + "?provider_type=dedicated")
        content = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        expected = [
            {'id': self.p3.id, 'access_key': self.p3.access_key,
            'provider_type': self.p3.provider_type, 'name': self.p3.name},
        ]
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_providers_by_type_not_found(self):
        '''Get providers for non-existent type'''
        response = self.client.get(self.path + "?provider_type=DUMMIEST")
        self.assertEquals(response.status_code, 200)
        expected = []
        self.assertEquals(json.loads(response.content), expected)

    def test_get_provider_by_id(self):
        '''Get a provider by id'''
        response = self.client.get(self.path + "2")
        self.assertEquals(response.status_code, 200)
        expected = {
            'id': self.p2.id, 'access_key': self.p2.access_key,
            'provider_type': self.p2.provider_type, 'name': self.p2.name,
        }
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_provider_by_id_not_found(self):
        '''Get a provider by wrong id'''
        response = self.client.get(self.path + '99999')
        self.assertEquals(response.status_code, 404)

    def test_get_provider_by_name(self):
        '''Get a provider by name'''
        response = self.client.get(self.path + "?name=prov1")
        self.assertEquals(response.status_code, 200)
        expected = {
            'id': self.p1.id, 'access_key': self.p1.access_key,
            'provider_type': self.p1.provider_type, 'name': self.p1.name
        }
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_provider_by_name_not_found(self):
        '''Get a provider by wrong name'''
        response = self.client.get(self.path + "?name=prov1nothere")
        self.assertEquals(response.status_code, 404)


class POSTProviderTest(TestCase):
    urls = 'overmind.test_urls'
    
    def setUp(self):
        self.path = "/api/providers/"
        self.client = Client()
    
    def test_create_provider(self):
        """Create a new provider"""
        data = {
            'name': 'A new provider',
            'provider_type': 'DUMMY',
            'access_key': 'kiuuuuuu',
        }
        resp = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp.status_code, 200)
        
        expected = data
        expected["id"] = 1
        self.assertEquals(json.loads(resp.content), expected)
        
        #Check that it really is in the DB
        p = Provider.objects.get(id=1)
        self.assertEquals(p.name, 'A new provider')
        self.assertEquals(p.provider_type, 'DUMMY')

    def test_missing_access_key(self):
        """Create a new provider with missing access_key"""
        data = {'name': 'A new provider', 'provider_type': 'DUMMY'}
        expected = "Bad Request\naccess_key: This field is required."
        resp = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, expected)
        data['access_key'] = ""
        resp = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, expected)
        
        # Make sure it wasn't saved in the DB
        self.assertEquals(len(Provider.objects.all()), 0)
