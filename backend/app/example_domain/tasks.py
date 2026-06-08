from app.core.celery import celery_app
from app.core.database import get_session
from app.example_domain import logger
from app.example_domain.models.example_resource import ExampleResource


@celery_app.task(name='example_domain.tasks.process_example_resource')
def process_example_resource(example_resource_id: int) -> None:
    """Process an example resource after it is created.

    Demonstrates the task conventions: a JSON-serializable argument (the id, never the ORM
    object) and a standalone ``get_session()`` session because the task runs outside the
    request lifecycle. Replace the body with whatever async work your resource needs.

    Args:
        example_resource_id: Id of the ``ExampleResource`` to process.
    """
    with get_session() as db:
        resource = db.get_or_404(ExampleResource, id=example_resource_id)
        logger.info('Processing example resource %s (%s)', resource.id, resource.name)
