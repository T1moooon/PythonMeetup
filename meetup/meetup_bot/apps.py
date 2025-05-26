from django.apps import AppConfig


class MeetupBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "meetup_bot"

    def ready(self):
        print('bot started')
        import meetup_bot.bot 
