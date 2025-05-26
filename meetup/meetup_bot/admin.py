from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages

# from .tasks import run_broadcast_message

from .models import CustomUser, Event, Talk, Question, Mailing, MailingReport


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


class QuestionInline(admin.TabularInline):  # или admin.StackedInline
    model = Question
    extra = 0


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'speaker', 'event', 'start_time', 'end_time')
    list_filter = ('event', 'speaker')
    search_fields = ('title', 'speaker__name')
    raw_id_fields = ('speaker', 'event')
    date_hierarchy = 'start_time'
    ordering = ('start_time',)
    inlines = (QuestionInline,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('talk', 'guest', 'short_text')
    
    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Краткий текст'


# Inline для отображения отчетов внутри Mailing
class MailingReportInline(admin.TabularInline):  # или admin.StackedInline
    model = MailingReport
    extra = 0  # Не показывать пустые формы для добавления
    readonly_fields = ('user', 'status')  # Если не хотим редактировать в админке
    can_delete = False  # Запретить удаление отчетов
    fields = ('user', 'status', 'mailing')  # Какие поля показывать


# Настройка админки для Mailing
@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'status_summary')  # Добавим сводку по статусам
    inlines = (MailingReportInline,)  # Подключаем Inline
    search_fields = ('text', 'users__username')  # Поиск по тексту и пользователям
    # autocomplete_fields = ('users',)

    # Метод для отображения сводки по статусам в списке рассылок
    def status_summary(self, obj):
        reports = obj.mailingreport_set.all()
        success = reports.filter(status='Success').count()
        fails = reports.filter(status='Fail').count()
        return f"✅{success} ❌{fails}"
    status_summary.short_description = 'Статусы'
