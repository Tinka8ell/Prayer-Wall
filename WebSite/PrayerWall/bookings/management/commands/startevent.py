from django.core.management.base import BaseCommand, CommandError
from bookings.models import Event #, EventManager
from datetime import datetime

def fromDatetimeString(string):
    return datetime.strptime(string, "%Y-%m-%d-%H")
#    return datetime.fromisoformat(string)

class Command(BaseCommand):
    help = 'Creates and populates a new Event'

    def add_arguments(self, parser):
        parser.add_argument('name', help="Event name")
        parser.add_argument('start', type=fromDatetimeString, help="Date and time of the start of the event in format: YYYY-MM-DD-HH")
        parser.add_argument('-length', type=int, default=24, help="Number of hour slots")
        parser.add_argument('locations', nargs='+', action='append', help="Location used as '(' NAME ',' [SIZE] ')' - can be multiple locations", type=tuple)

    def handle(self, *args, **options):
        name = options['name']
        start = options['start']
        length = options['length']
        locations = options['locations']
        Event.objects.create_event(name, start, locations, length=24)
        self.stdout.write(self.style.SUCCESS('Successfully created event "%s"' % name))
    