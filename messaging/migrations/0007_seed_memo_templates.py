from django.db import migrations

def seed_templates(apps, schema_editor):
    MemoTemplate = apps.get_model('messaging', 'MemoTemplate')
    templates = [
        {
            'title': 'Annual / Casual Leave Application',
            'category': 'HR & Staff Welfare',
            'default_priority': 'ROUTINE',
            'default_subject': 'Application for Annual / Casual Leave of Absence',
            'default_body': (
                "I hereby write to formally request approval for [Number] days of my annual/casual leave, "
                "effective from [Start Date] to [End Date].\n\n"
                "Reason for Request: [State specific reason or family commitment]\n\n"
                "Handover Arrangements: During my absence, all pending tasks and responsibilities of my desk "
                "will be covered by [Name of Relieving Colleague], [Position/Dept].\n\n"
                "Thank you for your consideration and approval."
            )
        },
        {
            'title': 'Response to Official Query',
            'category': 'HR & Administration',
            'default_priority': 'ROUTINE',
            'default_subject': 'Formal Response to Query Ref: [Insert Query Reference Number]',
            'default_body': (
                "With reference to the official query dated [Date] with reference number [Reference Number], "
                "I wish to submit my formal explanation as follows:\n\n"
                "1. Background & Context: [Explain the circumstances]\n"
                "2. Clarification of Facts: [State the exact occurrences and mitigating factors]\n"
                "3. Preventive / Corrective Measures: [Explain actions taken to prevent a recurrence]\n\n"
                "I remain committed to upholding the standards and service delivery of our council."
            )
        },
        {
            'title': 'Departmental Requisition / Approval Request',
            'category': 'Procurement & Finance',
            'default_priority': 'URGENT',
            'default_subject': 'Request for Approval / Provision of Office Consumables & Equipment',
            'default_body': (
                "I respectfully forward this requisition on behalf of the [Department Name] for the approval "
                "and procurement of the following essential items:\n\n"
                "- Item 1: [Description] - Qty: [X] - Estimated Cost: ₦[Amount]\n"
                "- Item 2: [Description] - Qty: [Y] - Estimated Cost: ₦[Amount]\n\n"
                "Justification: These materials are required to maintain ongoing operational efficiency.\n\n"
                "Kindly review and grant approval to enable Procurement action."
            )
        },
        {
            'title': 'Field Inspection & Status Report',
            'category': 'Technical & Operations',
            'default_priority': 'ROUTINE',
            'default_subject': 'Field Inspection Report on [Project / Location Name]',
            'default_body': (
                "Following the directive to carry out an on-site inspection, our team visited the site at [Location] on [Date].\n\n"
                "Key Observations & Findings:\n"
                "1. Current Physical Progress: [Progress percentage or description]\n"
                "2. Technical Defects / Challenges Identified: [List challenges]\n"
                "3. Vendor / Contractor Compliance: [Compliance summary]\n\n"
                "Recommendations:\n"
                "- [Recommendation 1]\n"
                "- [Recommendation 2]\n\n"
                "Submitted for your information and necessary administrative directives."
            )
        },
        {
            'title': 'Inter-Departmental Information & File Request',
            'category': 'General Administration',
            'default_priority': 'ROUTINE',
            'default_subject': 'Request for Departmental File Records / Information Concerning [Subject]',
            'default_body': (
                "We respectfully request the transmission of file records, statistics, or reports concerning "
                "[Subject / Topic] currently under your desk's custody.\n\n"
                "Purpose of Request: This information is required for [Compilation of monthly report / Budget preparation / Audit review].\n\n"
                "We would appreciate your cooperation in providing the documents on or before [Target Date]."
            )
        },
        {
            'title': 'Executive Council Administrative Directive',
            'category': 'Executive Office',
            'default_priority': 'URGENT',
            'default_subject': 'Executive Directive: Compliance with [Directive Name]',
            'default_body': (
                "By direction of the Council Manager / Council Administration, all Heads of Departments and Units "
                "are hereby instructed to implement the following measures immediately:\n\n"
                "1. [Action Point 1]\n"
                "2. [Action Point 2]\n\n"
                "A compliance report must be submitted to the Office of the Council Manager not later than [Deadline Date/Time].\n\n"
                "Strict compliance is required."
            )
        }
    ]
    for data in templates:
        MemoTemplate.objects.get_or_create(title=data['title'], defaults=data)

def reverse_seed(apps, schema_editor):
    MemoTemplate = apps.get_model('messaging', 'MemoTemplate')
    MemoTemplate.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('messaging', '0006_message_escalated_message_escalated_at_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_templates, reverse_seed),
    ]
