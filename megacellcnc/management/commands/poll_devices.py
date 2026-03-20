"""
Replaces Celery Beat for local development.

Polls all registered devices every N seconds (default 5), calling the same
check_device_status logic that Celery Beat would normally trigger.

Usage:
    python manage.py poll_devices            # poll every 5 seconds
    python manage.py poll_devices --interval 10   # poll every 10 seconds
    python manage.py poll_devices --once     # poll once and exit

In PyCharm you can create a second Run Configuration:
    Script path:  manage.py
    Parameters:   poll_devices
    Working dir:  <project root>
Then click Debug to set breakpoints inside tasks.py.
"""

import time

from django.core.management.base import BaseCommand

from megacellcnc.tasks import check_device_status
from megacellcnc.models import Device


class Command(BaseCommand):
    help = "Poll all Megacell devices in a loop (dev replacement for Celery Beat)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=5,
            help="Seconds between polls (default: 5)",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Poll once and exit (useful for quick debugging)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        once = options["once"]

        self.stdout.write(self.style.SUCCESS(
            f"Device poller started (interval={interval}s, once={once})"
        ))

        while True:
            devices = Device.objects.all()
            count = devices.count()

            if count == 0:
                self.stdout.write("No devices registered, waiting...")
            else:
                self.stdout.write(f"Polling {count} device(s)...")
                for device in devices:
                    try:
                        result = check_device_status(device.id)
                        status = "online" if result else "offline"
                        self.stdout.write(f"  {device.name} ({device.ip}): {status}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"  {device.name} ({device.ip}): ERROR - {e}"
                        ))

            if once:
                break

            time.sleep(interval)
