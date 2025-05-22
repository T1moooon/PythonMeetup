from django.db import models

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
def get_program(event_id):
    event = Event.objects.get(pk=event_id)
    talks = event.talks.all()
    return list(talks)

# Мероприятие Event
# Программа
# Доклад Talk
# Спикер и гости СustomUser
# Вопросы Question
