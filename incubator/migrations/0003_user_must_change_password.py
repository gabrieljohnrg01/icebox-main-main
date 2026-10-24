from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incubator', '0002_remove_startup_industry_remove_startup_stage'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='must_change_password',
            field=models.BooleanField(default=False),
        ),
    ]
