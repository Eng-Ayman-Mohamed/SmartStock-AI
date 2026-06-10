from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_category_remove_stocklevel_quantity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocklevel',
            name='quantity_reserved',
            field=models.IntegerField(default=0),
        ),
    ]
