from django.db import migrations

def update_council_departments(apps, schema_editor):
    Department = apps.get_model('accounts', 'Department')
    CustomUser = apps.get_model('accounts', 'CustomUser')
    ProcurementMemo = apps.get_model('accounts', 'ProcurementMemo')

    NEW_DEPARTMENTS = [
        ('Admin', 'CM'),
        ('HR/Admin', 'LINE'),
        ('Department of Works', 'LINE'),
        ('Agric', 'LINE'),
        ('Education', 'LINE'),
        ('Budget', 'BUDGET'),
        ('WAPA (Women Affairs and Poverty Alleviation)', 'LINE'),
        ('Health Care', 'LINE'),
        ('ICT', 'LINE'),
        ('Environment and Health', 'LINE'),
        ('Public Affairs', 'LINE'),
        ('Legal Department', 'LINE'),
        ('Audit Department', 'AUDIT'),
        ('Tourism', 'LINE'),
        ('Procurement', 'PROCUREMENT'),
        ('Chieftaincy', 'LINE'),
    ]

    canonical_map = {}
    for name, code in NEW_DEPARTMENTS:
        d, _ = Department.objects.get_or_create(name=name, defaults={'code': code})
        if d.code != code:
            d.code = code
            d.save()
        canonical_map[name] = d

    alias_map = {
        'The Office of the Council Manager': canonical_map['Admin'],
        'Office of the Council Manager': canonical_map['Admin'],
        'Budget Department': canonical_map['Budget'],
        'Women Affairs and Poverty Alleviation (WAPA)': canonical_map['WAPA (Women Affairs and Poverty Alleviation)'],
        'Human Affairs and Poverty Alleviation': canonical_map['WAPA (Women Affairs and Poverty Alleviation)'],
        'WAPA': canonical_map['WAPA (Women Affairs and Poverty Alleviation)'],
        'Health': canonical_map['Health Care'],
        'Information and Communications Technology (ICT)': canonical_map['ICT'],
        'Information': canonical_map['Public Affairs'],
        'Internal Audit Office': canonical_map['Audit Department'],
        'Tourism and Culture': canonical_map['Tourism'],
        'Procurement Department': canonical_map['Procurement'],
        'Pay Office / Treasury': canonical_map['Budget'],
        'Treasury (Pay Office)': canonical_map['Budget'],
    }

    for u in CustomUser.objects.all():
        if u.department and u.department.name in alias_map:
            u.department = alias_map[u.department.name]
            u.save()

    for m in ProcurementMemo.objects.all():
        if m.originating_department and m.originating_department.name in alias_map:
            m.originating_department = alias_map[m.originating_department.name]
            m.save()

    canonical_ids = [d.id for d in canonical_map.values()]
    Department.objects.exclude(id__in=canonical_ids).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_populate_canonical_departments'),
    ]

    operations = [
        migrations.RunPython(update_council_departments, migrations.RunPython.noop),
    ]
