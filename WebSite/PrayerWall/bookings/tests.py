from django.test import TestCase

# for management command testing
from io import StringIO
from django.core.management import call_command

# Create your tests for bookings here.


class StartEventTest(TestCase):
    def test_command_output(self):
        out = StringIO()
        call_command("startevent 'My New Event' 2020/11/27-20 ('online',) ('104', 2)", stdout=out)
        self.assertIn('Successfully created event "My New Event"', out.getvalue())
