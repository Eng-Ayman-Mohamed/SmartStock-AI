from django.contrib import admin

from .models import Notification, UserNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("type", "severity", "title", "created_at")
    list_filter = ("type", "severity")
    search_fields = ("title", "message")


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notification", "is_read", "read_at")
    list_filter = ("is_read",)
