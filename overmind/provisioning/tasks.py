from celery.decorators import task, periodic_task
from celery.task.sets import subtask
from libcloud.types import InvalidCredsException
from provisioning.models import Provider
from datetime import timedelta


@periodic_task(run_every=timedelta(seconds=30))
def update_providers(**kwargs):
    logger = update_providers.get_logger(**kwargs)
    logger.debug("Syncing providers...")
    for prov in Provider.objects.filter(ready=True):
        import_sizes.delay(prov.id)
        import_nodes.delay(prov.id)

@task()
def import_provider_info(provider_id, **kwargs):
    logger = import_provider_info.get_logger(**kwargs)
    prov = Provider.objects.get(id=provider_id)
    logger.debug('Importing info for provider %s...' % prov)
    import_images.delay(provider_id, callback=subtask(import_locations,
                                callback=subtask(import_sizes,
                                    callback=subtask(import_nodes))))

@task(ignore_result=True)
def import_images(provider_id, callback=None, **kwargs):
    logger = import_images.get_logger(**kwargs)
    prov = Provider.objects.get(id=provider_id)
    logger.debug('Importing images for provider %s...' % prov)
    prov.import_images()
    if callback:
        subtask(callback).delay(provider_id)

@task(ignore_result=True)
def import_locations(provider_id, callback=None, **kwargs):
    logger = import_locations.get_logger(**kwargs)
    prov = Provider.objects.get(id=provider_id)
    logger.debug('Importing locations for provider %s...' % prov)
    prov.import_locations()
    if callback:
        subtask(callback).delay(provider_id)

@task(ignore_result=True)
def import_sizes(provider_id, callback=None, **kwargs):
    logger = import_sizes.get_logger(**kwargs)
    prov = Provider.objects.get(id=provider_id)
    logger.debug('Importing sizes for provider %s...' % prov)
    prov.import_sizes()
    if callback:
        subtask(callback).delay(provider_id)


@task(ignore_result=True)
def import_nodes(provider_id, **kwargs):
    logger = import_nodes.get_logger(**kwargs)
    prov = Provider.objects.get(id=provider_id)
    logger.debug('Importing nodes for provider %s...' % prov)
    prov.import_nodes()
    if not prov.ready:
        prov.ready = True
        prov.save()
