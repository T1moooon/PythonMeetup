from django.db import models
from django.utils import timezone
from django.db.models import Q

from asgiref.sync import sync_to_async


class CustomUser(models.Model):
    ROLE_CHOICES = [
        ('guest', 'guest'),
        ('speaker', 'speaker'),
        ('organizer', 'organizer'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='guest',
        blank=True,
        null=True,
        help_text="User's role in the system"
    )
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'{self.role} {self.name}'


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Talk(models.Model):
    speaker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="talks"
    )
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(blank=True, null=True)
    actual_end_time = models.DateTimeField(blank=True, null=True)
    # description = models.TextField(max_length=200)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="talks"
    )

    def __str__(self):
        return f"{self.title} by {self.speaker.name}"


class Question(models.Model):
    text = models.CharField(max_length=250)
    guest = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='guest_questions'
    )
    speaker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        related_name='speaker_questions'
    )

    def __str__(self):
        return f"{self.text} by {self.guest.name} to {self.speaker.name}"


@sync_to_async
def get_users():
    return list(CustomUser.objects.all())


@sync_to_async
def get_user(telegram_id, name):
    try:
        user = CustomUser.objects.get(telegram_id=telegram_id, name=name)
        return user
    except CustomUser.DoesNotExist:
        return


@sync_to_async
def create_user(telegram_id, name, role):
    return CustomUser.objects.get_or_create(telegram_id=telegram_id, name=name, role=role)


@sync_to_async
def get_program(event_id=None):
    if event_id:
        event = Event.objects.get(pk=event_id)
    else:
        today = timezone.now().date()
        event = Event.objects.filter(
            start_date__date__lte=today,
            end_date__date__gte=today
        ).first()
    if event:
        talks = event.talks.all()
        return event, list(talks)
    return None, None


@sync_to_async
def get_talk(talk_id):
    talk = Talk.objects.select_related('speaker').get(pk=talk_id)
    return talk


@sync_to_async
def start_talk(talk_id):
    talk = Talk.objects.get(pk=talk_id)
    talk.actual_start_time = timezone.now()
    talk.actual_end_time = None
    talk.save()
    return talk


@sync_to_async
def end_talk(talk_id):
    talk = Talk.objects.get(pk=talk_id)
    talk.actual_end_time = timezone.now()
    talk.save()
    return talk


@sync_to_async
def get_current_talks():
    now = timezone.now()
    return list(Talk.objects.select_related('speaker').filter(
        actual_start_time__isnull=False,
        actual_end_time__isnull=True,
        start_time__lte=now,
        end_time__gte=now
    ))


# Мероприятие Event
# Программа
# Доклад Talk
# Спикер и гости СustomUser
# Вопросы Question
