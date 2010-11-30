from django.test import TestCase
import unittest
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from overmind.provisioning.models import Provider, Node
import simplejson as json
import copy, logging


class BaseProviderTestCase(TestCase):
    urls = 'overmind.test_urls'
    
    def setUp(self):
        self.path = "/api/providers/"
        
        op = Group.objects.get(name='Operator')
        self.user = User.objects.create_user(
            username='testuser', email='t@t.com', password='test1')
        self.user.groups.add(op)
        self.user.save()
        
        self.client = Client()
        #login = self.client.login(
        #username=self.user.username, password=self.user.password)
        #self.assertTrue(login)
    
    def create_provider(self):
        '''Utility function to create providers using the api'''
        data = {
            'name': 'A provider to be updated',
            'provider_type': 'DUMMY',
            'access_key': 'somekey',
        }
        resp_new = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp_new.status_code, 200)
        return json.loads(resp_new.content)


class ReadProviderTest(BaseProviderTestCase):
    def setUp(self):
        super(ReadProviderTest, self).setUp()
        
        self.p1 = Provider(name="prov1", provider_type="DUMMY", access_key="keyzz")
        self.p1.save()
        self.p2 = Provider(name="prov2", provider_type="DUMMY", access_key="keyzz2")
        self.p2.save()
        self.p3 = Provider(name="prov3", provider_type="dedicated")
        self.p3.save()
    
    def test_not_authenticated(self):
        '''A non authenticated user should get 401'''
        # NOTE: Use non-authenticated client
        response = self.client.get(self.path)
        self.assertEquals(response.status_code, 401)
    
    def test_get_all_providers(self):
        '''Should show all existing providers'''
        response = self.client.get(self.path)
        self.assertEquals(response.status_code, 200)
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
        '''Should return NOT_FOUND when requesting a provider with non existing id'''
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
        '''Should return NOT_FOUND when requesting a provider with a non existing name'''
        response = self.client.get(self.path + "?name=prov1nothere")
        self.assertEquals(response.status_code, 404)


class CreateProviderTest(BaseProviderTestCase):
    def test_create_provider(self):
        '''Should create a new provider when request is valid'''
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
    
    def test_create_provider_should_import_nodes(self):
        '''Should import nodes when a new provider is created'''
        # There shouldn't be any nodes in the DB
        self.assertEquals(len(Node.objects.all()), 0)
        data = {
            'name': 'A new provider',
            'provider_type': 'DUMMY',
            'access_key': 'kiuuuuuu',
        }
        resp = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        
        # There should be exactly 2 nodes in the DB now
        self.assertEquals(len(Node.objects.all()), 2)
    
    def test_create_provider_missing_access_key(self):
        """Should not create a new provider when access_key is missing"""
        data = {'name': 'A new provider', 'provider_type': 'DUMMY'}
        expected = "Bad Request\naccess_key: This field is required."
        resp = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, expected)
        
        # Make sure it wasn't saved in the DB
        self.assertEquals(len(Provider.objects.all()), 0)
    
    def test_create_provider_empty_access_key(self):
        '''Should not create a new provider when access_key is empty'''
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


class UpdateProviderTest(BaseProviderTestCase):
    def test_update_provider_name(self):
        '''Should update the provider name when request is valid'''
        # First create a provider
        new_data = self.create_provider()
        
        # Now update the newly added provider
        new_data['name'] = "ThisNameIsMuchBetter"
        resp = self.client.put(
            self.path + str(new_data["id"]), json.dumps(new_data), content_type='application/json')
        self.assertEquals(resp.status_code, 200)
        
        expected = new_data
        self.assertEquals(json.loads(resp.content), expected)
        
        #Check that it was also updated in the DB
        p = Provider.objects.get(id=new_data['id'])
        self.assertEquals(p.name, new_data['name'])
    
    def test_update_provider_missing_field(self):
        '''Should not update a provider when a field is missing'''
        # First create a provider
        new_data = self.create_provider()
        
        # Now try to update the provider while leaving out each field in turn
        for field in new_data:
            if field == "id": continue#field "id" is not required
            modified_data = copy.deepcopy(new_data)#Don't alter original data
            del modified_data[field]#remove a required field
            resp = self.client.put(
                self.path + str(new_data['id']),
                json.dumps(modified_data),
                content_type='application/json')
            expected = "Bad Request\n%s: This field is required." % field
            self.assertEquals(resp.status_code, 400)
            self.assertEquals(resp.content, expected)
    
    def test_update_provider_empty_field(self):
        """Should not update a provider when a field is empty"""
        # First create a provider
        new_data = self.create_provider()
        
        # Now try to update the provider while leaving out each field empty
        for field in new_data:
            if field == "id": continue#field "id" is not required
            modified_data = copy.deepcopy(new_data)#Don't alter original data
            modified_data[field] = ""#Make a field empty
            resp = self.client.put(
                self.path + str(new_data['id']),
                json.dumps(modified_data),
                content_type='application/json')
            expected = "Bad Request\n%s: This field is required." % field
            self.assertEquals(resp.status_code, 400)
            self.assertEquals(resp.content, expected)


class DeleteProviderTest(BaseProviderTestCase):
    def test_delete_provider(self):
        '''Should delete a provider'''
        # First create a provider
        new_data = self.create_provider()
        
        # Now delete the newly added provider
        resp = self.client.delete(self.path + str(new_data['id']))
        self.assertEquals(resp.status_code, 204)
        
        # Check that the api returns not found
        resp = self.client.get(self.path + str(new_data['id']))
        self.assertEquals(resp.status_code, 404, 'The API should return NOT_FOUND')
        
        # Check that it was also deleted from the DB
        try:
            Provider.objects.get(id=new_data['id'])
            self.fail('The provider was not deleted from the DB')
        except Provider.DoesNotExist:
            pass


class CreateImageTest(BaseProviderTestCase):
    def setUp(self):
        super(ReadImageTest, self).setUp()
        
        self.p1 = Provider(name="prov1", provider_type="DUMMY", access_key="keyzz")
        self.p1.save()
        self.p1.import_images()
        self.p2 = Provider(name="prov2", provider_type="DUMMY", access_key="keyzz2")
        self.p2.save()
        self.p2.import_images()
    
    def test_create_image_should_fail(self):
        '''Should return not allowed when trying to POST'''
        data = {"image_id": "10", "name": "myimage", "favorite": False,
            "provider_id": "1"}
        resp = self.client.post(
            self.path, json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 405)


class ReadImageTest(BaseProviderTestCase):
    def setUp(self):
        super(ReadImageTest, self).setUp()
        
        self.p1 = Provider(name="prov1", provider_type="DUMMY", access_key="keyzz")
        self.p1.save()
        self.p1.import_images()
        self.p2 = Provider(name="prov2", provider_type="DUMMY", access_key="keyzz2")
        self.p2.save()
        self.p2.import_images()
    
    def test_get_all_images(self):
        '''Should return all images for a given provider'''
        response = self.client.get(self.path + str(self.p1.id) + "/images/")
        self.assertEquals(response.status_code, 200)
        expected = [
            {"id": 1, "image_id": "1", "name": "Ubuntu 9.10", "favorite": False},
            {"id": 2,"image_id": "2","name": "Ubuntu 9.04", "favorite": False},
            {"id": 3, "image_id": "3", "name": "Slackware 4", "favorite": False},
        ]
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_image_by_id(self):
        '''Should show image with id=2'''
        response = self.client.get(self.path + str(self.p1.id) + "/images/2")
        self.assertEquals(response.status_code, 200)
        expected = {
            "id": 2,"image_id": "2","name": "Ubuntu 9.04", "favorite": False}
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_image_by_image_id(self):
        '''Should show image with image_id=2'''
        path = self.path + str(self.p1.id) + "/images/" + "?image_id=2"
        response = self.client.get(path)
        self.assertEquals(response.status_code, 200)
        expected = {
            "id": 2,"image_id": "2","name": "Ubuntu 9.04", "favorite": False}
        self.assertEquals(json.loads(response.content), expected)
    
    def test_get_image_by_name(self):
        '''Should show image with name=Ubuntu 9.04'''
        path = self.path + str(self.p1.id) + "/images/" + "?name=Ubuntu 9.04"
        response = self.client.get(path)
        self.assertEquals(response.status_code, 200)
        expected = {
            "id": 2,"image_id": "2","name": "Ubuntu 9.04", "favorite": False}
        self.assertEquals(json.loads(response.content), expected)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(CreateProviderTest))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ReadProviderTest))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(UpdateProviderTest))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DeleteProviderTest))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ReadImageTest))
    return suite
