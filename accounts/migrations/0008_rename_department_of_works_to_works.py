from django.db import migrations

def rename_to_works(apps, schema_editor):
    Department = apps.get_model('accounts', 'Department')
    d = Department.objects.filter(name='Department of Works').first()
    if d:
        d.name = 'Works'
        d.save()
    else:
        Department.objects.get_or_create(name='Works', defaults={'code': 'LINE'})

def backwards(apps, schema_editor):
    Department = apps.get_model('accounts', 'Department')
    d = Department.objects.filter(name='Works').first()
    if d:
        d.name = 'Department of Works'
        d.save()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_update_council_departments'),
    ]

    operations = [
        migrations.RunPython(rename_to_works, backwards),
    ]
