from django.db import migrations

def populate_departments(apps, schema_editor):
    Department = apps.get_model('accounts', 'Department')
    departments = [
        ('ICT', 'LINE'),
        ('Procurement', 'PROCUREMENT'),
        ('Budget', 'BUDGET'),
        ('The Office of the Council Manager', 'CM'),
        ('Internal Audit Office', 'AUDIT'),
        ('Treasury (Pay Office)', 'PAY_OFFICE'),
        ('Human Affairs and Poverty Alleviation', 'LINE'),
        ('Tourism and Culture', 'LINE'),
        ('Information', 'LINE'),
        ('Health', 'LINE'),
    ]
    for name, code in departments:
        Department.objects.get_or_create(name=name, defaults={'code': code})

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_customuser_position'),
    ]

    operations = [
        migrations.RunPython(populate_departments, migrations.RunPython.noop),
    ]
