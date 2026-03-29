"""
Celery Beat (django-celery-beat): Intervall für check_all_devices verwalten.
"""
from django_celery_beat.models import IntervalSchedule, PeriodicTask

CHECK_DEVICES_TASK = 'megacellcnc.tasks.check_all_devices'
# Name wie in bestehenden Backups / DB-Einträgen
CHECK_DEVICES_PERIODIC_NAME = 'check-devices-status-5s'

DEFAULT_INTERVAL_SECONDS = 5
MIN_INTERVAL_SECONDS = 5
MAX_INTERVAL_SECONDS = 3600

BEAT_INTERVAL_PRESETS = [5, 10, 15, 30, 60, 120, 300]


def get_beat_interval_choices(current_seconds):
    choices = list(BEAT_INTERVAL_PRESETS)
    c = int(current_seconds)
    if c not in choices and MIN_INTERVAL_SECONDS <= c <= MAX_INTERVAL_SECONDS:
        choices.append(c)
        choices.sort()
    return choices


def get_check_devices_interval_seconds():
    """Aktuelles Intervall in Sekunden (Anzeige / API)."""
    try:
        pt = PeriodicTask.objects.get(name=CHECK_DEVICES_PERIODIC_NAME)
    except PeriodicTask.DoesNotExist:
        return DEFAULT_INTERVAL_SECONDS

    if not pt.interval_id:
        return DEFAULT_INTERVAL_SECONDS

    iv = pt.interval
    if iv.period == IntervalSchedule.SECONDS:
        return int(iv.every)
    if iv.period == IntervalSchedule.MINUTES:
        return int(iv.every) * 60
    if iv.period == IntervalSchedule.HOURS:
        return int(iv.every) * 3600
    return DEFAULT_INTERVAL_SECONDS


def set_check_devices_interval_seconds(seconds):
    """Intervall setzen; nur Sekunden-basierte Schedules werden erzeugt."""
    s = int(seconds)
    if s < MIN_INTERVAL_SECONDS or s > MAX_INTERVAL_SECONDS:
        raise ValueError(
            f'Intervall muss zwischen {MIN_INTERVAL_SECONDS} und {MAX_INTERVAL_SECONDS} Sekunden liegen.'
        )

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=s,
        period=IntervalSchedule.SECONDS,
    )

    pt, created = PeriodicTask.objects.get_or_create(
        name=CHECK_DEVICES_PERIODIC_NAME,
        defaults={
            'task': CHECK_DEVICES_TASK,
            'interval': schedule,
            'enabled': True,
        },
    )
    if created:
        return

    pt.task = CHECK_DEVICES_TASK
    pt.interval = schedule
    pt.crontab = None
    pt.solar = None
    pt.clocked = None
    pt.enabled = True
    pt.save()


def ensure_default_check_devices_periodic_task():
    """Beim Start: Eintrag anlegen, falls noch keiner existiert (z. B. frische Installation)."""
    if PeriodicTask.objects.filter(name=CHECK_DEVICES_PERIODIC_NAME).exists():
        return
    set_check_devices_interval_seconds(DEFAULT_INTERVAL_SECONDS)
