from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group, Permission

class Command(BaseCommand):
    help = 'Creates predefined user Roles'

    def handle(self, *args, **options):
        auth_perms = ['add_user', 'change_user', 'delete_user']
        provisioning_perms = [
            'add_provider', 'change_provider', 'delete_provider',
            'add_node', 'change_node', 'delete_node',
        ]
        
        try:
            admin = Group.objects.get(name='Admin')
        except Group.DoesNotExist:
            admin = Group(name='Admin')
            admin.save()
        try:
            op = Group.objects.get(name='Operator')
        except Group.DoesNotExist:
            op = Group(name='Operator')
            op.save()
        
        for codename in auth_perms:
            admin.permissions.add(Permission.objects.get(codename=codename))
        
        for codename in provisioning_perms:
            admin.permissions.add(Permission.objects.get(codename=codename))
            op.permissions.add(Permission.objects.get(codename=codename))
        
        # Add an Observer role with no rights
        try:
            ob = Group.objects.get(name='Observer')
        except Group.DoesNotExist:
            ob = Group(name='Observer')
            ob.save()
        
        # Remove superuser status (if any exist) and add the user to the admin group
        superusers = User.objects.filter(is_superuser=True)
        for user in superusers:
            user.is_superuser = False
            user.save()
            user.groups = [admin]
        
        print('Successfully loaded permission groups')

