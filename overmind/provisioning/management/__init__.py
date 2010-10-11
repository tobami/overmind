"""
Creates predefined user Roles
"""
from django.db.models import signals
from django.core.management import call_command
from  overmind.provisioning import models as provisioning_app

def create_groups(app, created_models, verbosity, **kwargs):
    call_command("create_groups")

signals.post_syncdb.connect(
    create_groups,
    sender=provisioning_app,
    dispatch_uid ="overmind.provisioning.management.create_groups"
)
