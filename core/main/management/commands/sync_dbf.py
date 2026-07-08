from django.core.management.base import BaseCommand

from main.services.legacy.formula_sync import sync_formula
from main.services.legacy.production_sync import sync_production
from main.services.legacy.rm_sync import sync_rm_list, sync_rm_incoming


class Command(BaseCommand):
    help = "Mirrors legacy DBF data (formula, production, raw materials) into PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument(
            '--only',
            choices=['formula', 'production', 'rm'],
            help="Run only one sync instead of all three.",
        )

    def handle(self, *args, **options):
        only = options.get('only')

        def progress(msg):
            self.stdout.write(msg)

        try:
            if only in (None, 'formula'):
                sync_formula(progress)
            if only in (None, 'production'):
                sync_production(progress)
            if only in (None, 'rm'):
                sync_rm_list(progress)
                sync_rm_incoming(progress)

            self.stdout.write(self.style.SUCCESS("Sync completed successfully."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Critical Mirror Error: {e}"))
            raise