from django.test import TestCase
from django.test.client import Client
from provisioning.models import Provider, Node
import simplejson


class GETProviderTest(TestCase):
    def setUp(self):
        self.path = "/api/providers/"
        self.client = Client()
        self.p1 = Provider(name="prov1", provider_type="DUMMY", access_key="keyzz")
        self.p1.save()
        self.p2 = Provider(name="prov2", provider_type="DUMMY", access_key="keyzz2")
        self.p2.save()
    
    def test_get_all_providers(self):
        """Get all existing providers"""
        response = self.client.get(self.path)
        content = simplejson.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(content), 2)
        self.assertEquals(content[0]['name'], self.p1.name)
        self.assertEquals(content[1]['access_key'], self.p2.access_key)
    
    def test_get_providers_by_type(self):
        '''Get all providers of a particular type'''
        #TODO: implement me!
        pass

    def test_get_provider_by_id(self):
        '''Get a provider by id'''
        response = self.client.get(self.path + "2")
        self.assertEquals(response.status_code, 200)
        expected = {
            'access_key': self.p2.access_key, 'secret_key': self.p2.secret_key,
            'provider_type': self.p2.provider_type, 'id': self.p2.id, 'name': self.p2.name
        }
        self.assertEquals(simplejson.loads(response.content), expected)
    
    def test_get_provider_by_name(self):
        '''Get a provider by name'''
        #TODO: implement me!
        pass
    
    def test_get_provider_by_id_not_found(self):
        '''Get a provider by wrong id'''
        response = self.client.get(self.path + '3')
        self.assertEquals(response.status_code, 404)


class POSTProviderTest(TestCase):
    def setUp(self):
        self.path = "/api/providers/"
        self.client = Client()
    
    def test_create_provider(self):
        """Create a new provider"""
        data = simplejson.dumps({
            'name': 'A new provider',
            'provider_type': 'DUMMY',
            'access_key': 'kiuuuu',
        })
        expected = '''{
    "access_key": "kiuuuu", 
    "secret_key": "", 
    "id": 1, 
    "name": "A new provider", 
    "provider_type": "DUMMY"
}'''
        resp = self.client.post(self.path, data, content_type='application/json')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.content, expected)
        #Check that it really is in the DB
        p = Provider.objects.get(id=1)
        self.assertEquals(p.name, 'A new provider')
        self.assertEquals(p.provider_type, 'DUMMY')

    def test_missing_key(self):
        """Create a new provider with missing access_key"""
        data = {'name': 'A new provider', 'provider_type': 'DUMMY'}
        expected = "Bad Request: access_key is a required field"
        resp = self.client.post(
            self.path, simplejson.dumps(data), content_type='application/json')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, expected)
        data['access_key'] = ""
        resp = self.client.post(
            self.path, simplejson.dumps(data), content_type='application/json')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, expected)
        # Make sure it wasn't saved in the DB
        self.assertEquals(len(Provider.objects.all()), 0)
