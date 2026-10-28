from django.db import migrations

def update_departments(apps, schema_editor):
    Department = apps.get_model('accounts', 'Department')
    CustomUser = apps.get_model('accounts', 'CustomUser')
    ProcurementMemo = apps.get_model('accounts', 'ProcurementMemo')

    ocm, _ = Department.objects.get_or_create(
        name='Office of the Council Manager',
        defaults={'code': 'CM'}
    )
    if ocm.code != 'CM':
        ocm.code = 'CM'
        ocm.save()

    hr_admin, _ = Department.objects.get_or_create(
        name='HR/Admin',
        defaults={'code': 'LINE'}
    )

    admin_dept = Department.objects.filter(name='Admin').first()
    if admin_dept:
        for u in CustomUser.objects.filter(department=admin_dept):
            if u.role == 'ADMIN' or u.is_superuser:
                u.department = ocm
            else:
                u.department = hr_admin
            u.save()

        for m in ProcurementMemo.objects.filter(originating_department=admin_dept):
            m.originating_department = ocm
            m.save()

        admin_dept.delete()

def backwards(apps, schema_editor):
    Department = apps.get_model('accounts', 'Department')
    Department.objects.get_or_create(name='Admin', defaults={'code': 'CM'})

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_rename_audit_and_legal'),
    ]

    operations = [
        migrations.RunPython(update_departments, backwards),
    ]
