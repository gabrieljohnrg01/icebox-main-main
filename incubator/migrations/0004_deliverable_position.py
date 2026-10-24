from django.db import migrations, models


def populate_deliverable_positions(apps, schema_editor):
    Deliverable = apps.get_model('incubator', 'Deliverable')
    Milestone = apps.get_model('incubator', 'Milestone')
    database = schema_editor.connection.alias

    milestone_ids = list(Milestone.objects.using(database).values_list('id', flat=True))
    for milestone_id in milestone_ids:
        deliverables = list(
            Deliverable.objects.using(database)
            .filter(milestone_id=milestone_id)
            .order_by('id')
        )
        for position, deliverable in enumerate(deliverables):
            deliverable.position = position
        if deliverables:
            Deliverable.objects.using(database).bulk_update(deliverables, ['position'])


class Migration(migrations.Migration):

    dependencies = [
        ('incubator', '0003_user_must_change_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverable',
            name='position',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='deliverable',
            options={'ordering': ('position', 'id')},
        ),
        migrations.RunPython(populate_deliverable_positions, migrations.RunPython.noop),
    ]
