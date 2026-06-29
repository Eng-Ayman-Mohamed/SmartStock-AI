from django.db import migrations


def create_system_bot(apps, schema_editor):
    User = apps.get_model('authentication', 'CustomUser')
    User.objects.get_or_create(
        email='system@smartstock.ai',
        defaults={
            'username': 'system-bot',
            'role': 'admin',
            'is_active': True,
            'email_verified': True,
            'password': '!',
        },
    )


def reverse(apps, schema_editor):
    User = apps.get_model('authentication', 'CustomUser')
    User.objects.filter(email='system@smartstock.ai').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0005_verify_existing_dev_users'),
    ]

    operations = [
        migrations.RunPython(create_system_bot, reverse),
    ]
