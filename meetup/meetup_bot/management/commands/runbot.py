from django.core.management.base import BaseCommand
import asyncio

from ...bot import main


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        asyncio.run(main())
