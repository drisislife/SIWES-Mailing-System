from django.db import migrations

def rename_audit_and_legal(apps, schema_editor):
    Department = apps.get_model('accounts', 'Department')
    for old, new in [('Audit Department', 'Audit'), ('Legal Department', 'Legal')]:
        d = Department.objects.filter(name=old).first()
        if d:
            d.name = new
            d.save()
        else:
            Department.objects.get_or_create(
                name=new,
                defaults={'code': 'AUDIT' if new == 'Audit' else 'LINE'}
            )

def backwards(apps, schema_editor):
    Department = apps.get_model('accounts', 'Department')
    for old, new in [('Audit', 'Audit Department'), ('Legal', 'Legal Department')]:
        d = Department.objects.filter(name=old).first()
        if d:
            d.name = new
            d.save()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_rename_department_of_works_to_works'),
    ]

    operations = [
        migrations.RunPython(rename_audit_and_legal, backwards),
    ]
