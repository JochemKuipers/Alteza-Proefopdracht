from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Post reset the database"

    def handle(self, *args, **options):
        self.stdout.write("Changing site host to localhost:8000")
        Site.objects.update(domain="localhost:8000", name="localhost")

        self.stdout.write("Creating new superuser...")
        User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin"
        )
