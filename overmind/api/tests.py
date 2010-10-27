from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from provisioning.models import Provider, Node
import simplejson as json


class ReadProviderTest(TestCase):
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
        '''Should show all existing providers'''
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
        '''Should show all providers of type DUMMY'''
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
        '''Should show all providers of type dedicated'''
        response = self.client.get(self.path + "?provider_type=dedicated")
        content = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        expected = [
            {'id': self.p3.id, 'access_key': self.p3.access_key,
            'provider_type': self.p3.provider_type, 'name': self.p3.name},
        ]
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_providers_by_type_not_found(self):
        '''Should show providers for non-existent type'''
        response = self.client.get(self.path + "?provider_type=DUMMIEST")
        self.assertEquals(response.status_code, 200)
        expected = []
        self.assertEquals(json.loads(response.content), expected)

    def test_get_provider_by_id(self):
        '''Should show provider with id=2'''
        response = self.client.get(self.path + "2")
        self.assertEquals(response.status_code, 200)
        expected = {
            'id': self.p2.id, 'access_key': self.p2.access_key,
            'provider_type': self.p2.provider_type, 'name': self.p2.name,
        }
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_provider_by_id_not_found(self):
        '''Should return NOT_FOUND because we requested a provider with non existing id'''
        response = self.client.get(self.path + '99999')
        self.assertEquals(response.status_code, 404)

    def test_get_provider_by_name(self):
        '''Should show provider with name "prov1"'''
        response = self.client.get(self.path + "?name=prov1")
        self.assertEquals(response.status_code, 200)
        expected = {
            'id': self.p1.id, 'access_key': self.p1.access_key,
            'provider_type': self.p1.provider_type, 'name': self.p1.name
        }
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_provider_by_name_not_found(self):
        '''Should return NOT_FOUND because we requested a provider with a non existing name'''
        response = self.client.get(self.path + "?name=prov1nothere")
        self.assertEquals(response.status_code, 404)


class CreateProviderTest(TestCase):
    urls = 'overmind.test_urls'
    
    def setUp(self):
        self.path = "/api/providers/"
        self.client = Client()
    
    def test_create_provider(self):
        """Should create a new provider"""
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

    def test_create_provider_missing_access_key(self):
        """Should not create a new provider if access_key is missing"""
        data = {'name': 'A new provider', 'provider_type': 'DUMMY'}
        expected = "Bad Request\naccess_key: This field is required."
        resp = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, expected)
        
        # Make sure it wasn't saved in the DB
        self.assertEquals(len(Provider.objects.all()), 0)

    def test_create_provider_empty_access_key(self):
        """Should not create a new provider if access_key is empty"""
        data = {'name': 'A new provider', 
                'provider_type': 'DUMMY',
                'access_key': '',
        }
        expected = "Bad Request\naccess_key: This field is required."
        resp = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, expected)

        # Make sure it wasn't saved in the DB
        self.assertEquals(len(Provider.objects.all()), 0)

class UpdateProviderTest(TestCase):
    urls = 'overmind.test_urls'
    
    def setUp(self):
        self.path = "/api/providers/"
        self.client = Client()
    
    def test_update_provider_name(self):
        """Should update the provider name"""
        # first let's create a provider
        initial_provider_count = len(Provider.objects.all())
        data = {
            'name': 'A provider to be updated',
            'provider_type': 'DUMMY',
            'access_key': 'somekey2',
        }
        resp_new = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp_new.status_code, 200)
        new_data = json.loads(resp_new.content)
        # check that it was added to the DB
        self.assertEquals(len(Provider.objects.all()), initial_provider_count+1)

        # now update the newly added provider
        id = new_data["id"]
        new_name = "ThisNameIsMuchBetter"
        data_updated = {
            'name': new_name,
            'access_key': 'somekey2',
        }
        resp = self.client.put(
            self.path + str(id), json.dumps(data_updated), content_type='application/json')
        self.assertEquals(resp.status_code, 200)

        data["name"] = new_name
        data["id"] = id
        expected = data
        self.assertEquals(json.loads(resp.content), expected)

        #Check that it was also updated in the DB
        p = Provider.objects.get(id=id)
        self.assertEquals(p.name, new_name)

    def test_update_provider_missing_access_key(self):
        """Should not update a provider if access_key is missing"""
        # first let's create a provider
        initial_provider_count = len(Provider.objects.all())
        data = {
            'name': 'A provider to be updated',
            'provider_type': 'DUMMY',
            'access_key': 'somekey',
        }
        resp_new = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp_new.status_code, 200)
        new_data = json.loads(resp_new.content)
        # check that it was added to the DB
        self.assertEquals(len(Provider.objects.all()), initial_provider_count+1)

        # now try to update the provider while not specifying an access key
        id = new_data["id"]
        new_name = "ThisNameIsMuchBetter"
        data_updated = {
            'name': new_name,
        }
        resp = self.client.put(
            self.path + str(id), json.dumps(data_updated), content_type='application/json')

        self.assertEquals(resp.status_code, 400)

    def test_update_provider_empty_access_key(self):
        """Should not update a provider if access_key is empty"""
        # first let's create a provider
        initial_provider_count = len(Provider.objects.all())
        data = {
            'name': 'A provider to be updated',
            'provider_type': 'DUMMY',
            'access_key': 'somekey',
        }
        resp_new = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp_new.status_code, 200)
        new_data = json.loads(resp_new.content)
        # check that it was added to the DB
        self.assertEquals(len(Provider.objects.all()), initial_provider_count+1)

        # now try to update the provider while specifying an empty access key
        id = new_data["id"]
        new_name = "ThisNameIsMuchBetter"
        data_updated = {
            'name': new_name,
            'access_key': '',
        }
        resp = self.client.put(
            self.path + str(id), json.dumps(data_updated), content_type='application/json')

        self.assertEquals(resp.status_code, 400)

    def test_update_provider_wrong_access_key(self):
        """Should not update a provider if access_key is wrong"""
        # first let's create a provider
        initial_provider_count = len(Provider.objects.all())
        data = {
            'name': 'A provider to be updated',
            'provider_type': 'DUMMY',
            'access_key': 'somekey',
        }
        resp_new = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp_new.status_code, 200)
        new_data = json.loads(resp_new.content)
        # check that it was added to the DB
        self.assertEquals(len(Provider.objects.all()), initial_provider_count+1)

        # now try to update the provider while specifying the wrong access key
        id = new_data["id"]
        new_name = "ThisNameIsMuchBetter"
        data_updated = {
            'name': new_name,
            'access_key': 'somewrongkey',
        }
        resp = self.client.put(
            self.path + str(id), json.dumps(data_updated), content_type='application/json')

        expected = "Bad Request: bad value %s for access_key" % data_updated['access_key']
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, expected)


class DeleteProviderTest(TestCase):
    urls = 'overmind.test_urls'
    
    def setUp(self):
        self.path = "/api/providers/"
        self.client = Client()
    
    def test_delete_provider(self):
        """Should delete a provider"""
        # first let's create a provider
        initial_provider_count = len(Provider.objects.all())
        data = {
            'name': 'A brand new provider',
            'provider_type': 'DUMMY',
            'access_key': 'somekey',
        }
        resp_new = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp_new.status_code, 200)
        new_data = json.loads(resp_new.content)
        # check that it was added to the DB
        self.assertEquals(len(Provider.objects.all()), initial_provider_count+1)

        # now delete the newly added provider
        id = new_data["id"]
        resp = self.client.delete(self.path + str(id))
        self.assertEquals(resp.status_code, 204)
        # check that it was also deleted from the DB
        self.assertEquals(len(Provider.objects.all()), initial_provider_count)

