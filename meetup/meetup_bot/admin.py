from django.contrib import admin

from .models import CustomUser, Event, Talk, Question


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'telegram_id', 'role')
    list_filter = ('role',)
    search_fields = ('name', 'telegram_id')
    ordering = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date')
    list_filter = ('start_date',)
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'speaker', 'event', 'start_time', 'end_time')
    list_filter = ('event', 'speaker')
    search_fields = ('title', 'speaker__name')
    raw_id_fields = ('speaker', 'event')
    date_hierarchy = 'start_time'
    ordering = ('start_time',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # list_display = ('text', 'guest', 'speaker', 'short_text')
    # list_filter = ('speaker', 'guest')
    # search_fields = ('text', 'guest__name', 'speaker__name')
    # raw_id_fields = ('guest', 'speaker')
    pass
    
    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Краткий текст'

# Register your models here.
