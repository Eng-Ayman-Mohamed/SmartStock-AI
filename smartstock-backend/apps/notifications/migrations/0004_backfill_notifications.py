from django.db import migrations


def backfill_notifications(apps, schema_editor):
    Notification = apps.get_model('notifications', 'Notification')
    UserNotification = apps.get_model('notifications', 'UserNotification')
    DashboardBanner = apps.get_model('monitoring', 'DashboardBanner')
    EscalationNotification = apps.get_model('notifications', 'EscalationNotification')
    User = apps.get_model('authentication', 'CustomUser')

    # Skip if already backfilled
    if Notification.objects.filter(metadata__source='backfill_dashboard_banner').exists():
        return

    users = list(User.objects.filter(is_active=True))

    # Backfill DashboardBanner -> Notification (type=monitoring)
    level_to_severity = {'info': 'info', 'warning': 'warning', 'error': 'critical'}
    banners = DashboardBanner.objects.all()
    banner_notifications = []
    for banner in banners:
        n = Notification(
            type='monitoring',
            severity=level_to_severity.get(banner.level, 'info'),
            title=banner.title,
            message=banner.message,
            metadata={
                'banner_id': banner.id,
                'alert_event_id': banner.alert_event_id,
                'source': 'backfill_dashboard_banner',
            },
        )
        n.save()
        # Update created_at after save (bypasses auto_now_add)
        Notification.objects.filter(pk=n.pk).update(created_at=banner.created_at)
        banner_notifications.append(n)

    # Backfill EscalationNotification -> Notification (type=escalation)
    escalations = EscalationNotification.objects.all()
    esc_notifications = []
    for esc in escalations:
        reason_display = (
            esc.get_reason_display() if hasattr(esc, 'get_reason_display') else esc.reason
        )
        n = Notification(
            type='escalation',
            severity='critical',
            title=f'PO Escalation: {reason_display}',
            message=esc.message or f'Escalation for PO {esc.po_id}: {reason_display}',
            metadata={
                'escalation_id': esc.id,
                'po_id': esc.po_id,
                'reason': esc.reason,
                'channel': esc.channel,
                'source': 'backfill_escalation_notification',
            },
        )
        n.save()
        Notification.objects.filter(pk=n.pk).update(created_at=esc.created_at)
        esc_notifications.append(n)

    # Create UserNotification for all active users
    all_new = banner_notifications + esc_notifications
    user_notifications = []
    for notif in all_new:
        for user in users:
            user_notifications.append(
                UserNotification(user=user, notification=notif, is_read=False)
            )
    UserNotification.objects.bulk_create(user_notifications, ignore_conflicts=True)


def reverse_backfill(apps, schema_editor):
    Notification = apps.get_model('notifications', 'Notification')
    UserNotification = apps.get_model('notifications', 'UserNotification')
    UserNotification.objects.filter(notification__metadata__source__startswith='backfill_').delete()
    Notification.objects.filter(metadata__source__startswith='backfill_').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0003_notification_usernotification_and_more'),
        ('monitoring', '0001_initial'),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_notifications, reverse_backfill),
    ]
