from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Creates predefined user Roles'

    def handle(self, *args, **options):
        auth_perms = ['add_user', 'change_user', 'delete_user']
        provisioning_perms = [
            'add_provider', 'change_provider', 'delete_provider',
            'add_node', 'change_node', 'delete_node',
        ]
        
        admin = Group(name='Admin')
        admin.save()
        op = Group(name='Operator')
        op.save()
        
        for codename in auth_perms:
            admin.permissions.add(Permission.objects.get(codename=codename))
        
        for codename in provisioning_perms:
            admin.permissions.add(Permission.objects.get(codename=codename))
            op.permissions.add(Permission.objects.get(codename=codename))
        
        ob = Group(name='Observer')
        ob.save()
        
        print('Successfully loaded permission groups')
        
        #TODO: if superuser (admin) user exists,
        # remove superuser status and add it to the group "Admin"
        
