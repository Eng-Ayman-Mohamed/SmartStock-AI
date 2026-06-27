from django.contrib.auth.hashers import make_password
from django.db import migrations


def verify_dev_users(apps, schema_editor):
    User = apps.get_model('authentication', 'CustomUser')
    for u in User.objects.filter(
        email__in=['admin@smartstock.ai', 'manager@smartstock.ai', 'viewer@smartstock.ai']
    ):
        changed = False
        if not u.email_verified:
            u.email_verified = True
            changed = True
        if u.email == 'admin@smartstock.ai':
            u.password = make_password('SmartStock2026!')
            changed = True
        if changed:
            u.save(update_fields=['email_verified', 'password'])


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0004_customuser_email_verified_emailverificationtoken'),
    ]

    operations = [
        migrations.RunPython(verify_dev_users, reverse),
    ]
