from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser, Department
from messaging.models import Message, MessageMinute, MessageAcknowledgement, NoticeBoardItem


class Command(BaseCommand):
    help = 'Seeds realistic council departments, mock personnel across all tiers, sample memos, and bulletin notices for testing and demonstration.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='CouncilPass123!',
            help='Default password for all seeded accounts (default: CouncilPass123!)'
        )

    def handle(self, *args, **options):
        password = options['password']
        self.stdout.write(self.style.NOTICE("Starting council test data seeding..."))

        # -------------------------------------------------------------------
        # 1. Departments
        # -------------------------------------------------------------------
        dept_data = [
            ("Office of the Council Manager", "CM"),
            ("HR/Admin", "LINE"),
            ("ICT", "LINE"),
            ("Works", "LINE"),
            ("Procurement", "PROCUREMENT"),
            ("Audit", "AUDIT"),
            ("Legal", "LINE"),
            ("Budget", "BUDGET"),
            ("Health Care", "LINE"),
            ("Education", "LINE"),
            ("Environment and Health", "LINE"),
            ("Public Affairs", "LINE"),
            ("WAPA (Women Affairs and Poverty Alleviation)", "LINE"),
            ("Agric", "LINE"),
            ("Tourism", "LINE"),
            ("Chieftaincy", "LINE"),
        ]

        depts = {}
        for name, code in dept_data:
            dept, _ = Department.objects.get_or_create(name=name, defaults={'code': code})
            if not dept.code:
                dept.code = code
                dept.save(update_fields=['code'])
            depts[name] = dept

        self.stdout.write(self.style.SUCCESS(f"Verified {len(depts)} canonical departments."))

        # -------------------------------------------------------------------
        # 2. Users (Council Leadership, HODs, and Staff)
        # -------------------------------------------------------------------
        users_config = [
            # Council Manager (Executive Admin)
            {
                'email': 'cm@council.gov.ng',
                'username': 'council_manager',
                'first_name': 'Rashidat',
                'last_name': 'Adeleke',
                'role': 'ADMIN',
                'department': depts['Office of the Council Manager'],
                'position': 'Council Manager / Head of Administration',
                'duty_status': 'ACTIVE',
                'duty_note': 'On seat in Executive Chamber.',
            },
            # HR & Admin
            {
                'email': 'hod.hr@council.gov.ng',
                'username': 'hod_hr',
                'first_name': 'Folashade',
                'last_name': 'Balogun',
                'role': 'HOD',
                'department': depts['HR/Admin'],
                'position': 'Head of Department, HR & Admin',
                'duty_status': 'ACTIVE',
                'duty_note': 'Available for official minutes.',
            },
            {
                'email': 'staff.hr@council.gov.ng',
                'username': 'staff_hr',
                'first_name': 'Tunde',
                'last_name': 'Bakare',
                'role': 'STAFF',
                'department': depts['HR/Admin'],
                'position': 'Senior Personnel Officer',
                'duty_status': 'ACTIVE',
                'duty_note': 'Processing promotion documentation.',
            },
            # ICT
            {
                'email': 'hod.ict@council.gov.ng',
                'username': 'hod_ict',
                'first_name': 'Damilola',
                'last_name': 'Idris',
                'role': 'HOD',
                'department': depts['ICT'],
                'position': 'Head of Information & Communication Technology',
                'duty_status': 'ACTIVE',
                'duty_note': 'Overseeing system migration & training.',
            },
            {
                'email': 'staff.ict@council.gov.ng',
                'username': 'staff_ict',
                'first_name': 'Chinedu',
                'last_name': 'Eze',
                'role': 'STAFF',
                'department': depts['ICT'],
                'position': 'Systems & Network Engineer',
                'duty_status': 'ACTIVE',
                'duty_note': 'Hardware and network maintenance.',
            },
            # Works & Infrastructure
            {
                'email': 'hod.works@council.gov.ng',
                'username': 'hod_works',
                'first_name': 'Mustapha',
                'last_name': 'Bello',
                'role': 'HOD',
                'department': depts['Works'],
                'position': 'Head of Department, Works & Housing',
                'duty_status': 'OFFICIAL_ASSIGNMENT',
                'duty_note': 'Site inspection at Local Market Project.',
            },
            {
                'email': 'staff.works@council.gov.ng',
                'username': 'staff_works',
                'first_name': 'Kabiru',
                'last_name': 'Alabi',
                'role': 'STAFF',
                'department': depts['Works'],
                'position': 'Civil Project Engineer II',
                'duty_status': 'OFFICIAL_ASSIGNMENT',
                'duty_note': 'Drainage survey in Ward 3.',
            },
            # Procurement
            {
                'email': 'hod.procurement@council.gov.ng',
                'username': 'hod_procurement',
                'first_name': 'Ngozi',
                'last_name': 'Okonkwo',
                'role': 'HOD',
                'department': depts['Procurement'],
                'position': 'Head of Procurement Unit',
                'duty_status': 'ACTIVE',
                'duty_note': 'Tenders board review in progress.',
            },
            {
                'email': 'staff.procurement@council.gov.ng',
                'username': 'staff_procurement',
                'first_name': 'Ayomide',
                'last_name': 'Bilesanmi',
                'role': 'STAFF',
                'department': depts['Procurement'],
                'position': 'Procurement Desk Officer',
                'duty_status': 'ACTIVE',
                'duty_note': 'Vendor evaluation ongoing.',
            },
            # Audit
            {
                'email': 'hod.audit@council.gov.ng',
                'username': 'hod_audit',
                'first_name': 'Samuel',
                'last_name': 'Adelekan',
                'role': 'HOD',
                'department': depts['Audit'],
                'position': 'Chief Internal Auditor',
                'duty_status': 'ACTIVE',
                'duty_note': 'Q3 Revenue and Expenditure verification.',
            },
            # Legal
            {
                'email': 'hod.legal@council.gov.ng',
                'username': 'hod_legal',
                'first_name': 'Amaka',
                'last_name': 'Obi',
                'role': 'HOD',
                'department': depts['Legal'],
                'position': 'Legal Officer / Counsel to the Council',
                'duty_status': 'OFFICIAL_ASSIGNMENT',
                'duty_note': 'High Court session representation.',
            },
            # Budget & Planning
            {
                'email': 'hod.budget@council.gov.ng',
                'username': 'hod_budget',
                'first_name': 'Babatunde',
                'last_name': 'Jinadu',
                'role': 'HOD',
                'department': depts['Budget'],
                'position': 'Head of Budget & Fiscal Planning',
                'duty_status': 'ACTIVE',
                'duty_note': 'Harmonizing annual budget proposals.',
            },
            # Health Care
            {
                'email': 'hod.health@council.gov.ng',
                'username': 'hod_health',
                'first_name': 'Kelechi',
                'last_name': 'Nwosu',
                'role': 'HOD',
                'department': depts['Health Care'],
                'position': 'Medical Officer of Health (MOH)',
                'duty_status': 'ACTIVE',
                'duty_note': 'Immunization campaign rollout.',
            },
            # WAPA
            {
                'email': 'hod.wapa@council.gov.ng',
                'username': 'hod_wapa',
                'first_name': 'Mariam',
                'last_name': 'Sanni',
                'role': 'HOD',
                'department': depts['WAPA (Women Affairs and Poverty Alleviation)'],
                'position': 'Head of Department, WAPA',
                'duty_status': 'ON_LEAVE',
                'duty_note': 'Annual statutory leave (Resumes 24th Nov).',
            },
        ]

        seeded_users = {}
        for uconf in users_config:
            email = uconf['email']
            user, created = CustomUser.objects.get_or_create(email=email, defaults={
                'username': uconf['username'],
                'first_name': uconf['first_name'],
                'last_name': uconf['last_name'],
                'role': uconf['role'],
                'department': uconf['department'],
                'position': uconf['position'],
                'duty_status': uconf['duty_status'],
                'duty_note': uconf['duty_note'],
                'account_approved': True,
                'is_active': True,
            })
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"  + Created {uconf['role']} {email} ({uconf['first_name']} {uconf['last_name']})")
            else:
                user.first_name = uconf['first_name']
                user.last_name = uconf['last_name']
                user.role = uconf['role']
                user.department = uconf['department']
                user.position = uconf['position']
                user.duty_status = uconf['duty_status']
                user.duty_note = uconf['duty_note']
                user.account_approved = True
                if not user.check_password(password):
                    user.set_password(password)
                user.save()
                self.stdout.write(f"  * Updated {uconf['role']} {email}")
            seeded_users[email] = user

        # -------------------------------------------------------------------
        # 3. Sample Memos (Covering Intra, Cross-Dept, Threads, Recalls)
        # -------------------------------------------------------------------
        u_cm = seeded_users['cm@council.gov.ng']
        u_hod_hr = seeded_users['hod.hr@council.gov.ng']
        u_staff_hr = seeded_users['staff.hr@council.gov.ng']
        u_hod_ict = seeded_users['hod.ict@council.gov.ng']
        u_staff_ict = seeded_users['staff.ict@council.gov.ng']
        u_hod_works = seeded_users['hod.works@council.gov.ng']
        u_staff_works = seeded_users['staff.works@council.gov.ng']
        u_hod_prc = seeded_users['hod.procurement@council.gov.ng']

        # Memo 1: Approved Intra-Department Memo with Read Receipt & Acknowledgement
        memo1, created1 = Message.objects.get_or_create(
            sender=u_staff_hr,
            recipient=u_hod_hr,
            subject='Submission of Consolidated Staff Leave Roster (Q4)',
            defaults={
                'priority': 'ROUTINE',
                'status': 'approved',
                'is_read': True,
                'read_at': timezone.now(),
                'body': (
                    "Memorandum for consideration and approval.\n\n"
                    "Forwarded herewith is the consolidated Fourth Quarter statutory leave schedule "
                    "for staff across all operational cadres. Adequate relief arrangements have been "
                    "put in place to forestall administrative bottlenecks.\n\n"
                    "Respectfully submitted for your formal minute and endorsement."
                )
            }
        )
        if created1:
            MessageMinute.objects.create(
                message=memo1,
                officer=u_hod_hr,
                comment="Approved as submitted. Forward extract to Accounts and Audit for administrative compliance."
            )
            MessageAcknowledgement.objects.create(
                message=memo1,
                acknowledged_by=u_hod_hr,
                note="Leave roster received, endorsed, and scheduled for execution."
            )
            self.stdout.write("  + Created approved intra-department memo with minutes & acknowledgement.")

        # Memo 2: Cross-Department Thread (Procurement -> Council Manager -> Reply)
        memo2, created2 = Message.objects.get_or_create(
            sender=u_hod_prc,
            recipient=u_cm,
            subject='Request for Executive Concurrence: Bi-Annual Procurement Plan',
            defaults={
                'priority': 'URGENT',
                'status': 'approved',
                'is_read': True,
                'read_at': timezone.now(),
                'body': (
                    "The Council Manager,\n\n"
                    "In line with the State Public Procurement Law, find attached the finalized bi-annual "
                    "procurement schedule covering office automation, health center supplies, and road grading materials.\n\n"
                    "Your executive concurrence is requested to proceed with tender notices."
                )
            }
        )
        if created2:
            MessageMinute.objects.create(
                message=memo2,
                officer=u_cm,
                comment="Concurred. Ensure strict adherence to Due Process thresholds and prompt public advertising."
            )
            Message.objects.create(
                sender=u_cm,
                recipient=u_hod_prc,
                parent=memo2,
                subject='Re: Request for Executive Concurrence: Bi-Annual Procurement Plan',
                priority='URGENT',
                status='approved',
                is_read=True,
                read_at=timezone.now(),
                body=(
                    "The Head of Procurement Unit,\n\n"
                    "Executive concurrence is granted as minuted on the parent document. "
                    "Liaise with Internal Audit for prior vetting before bid issuance."
                )
            )
            self.stdout.write("  + Created cross-department thread (Procurement to CM with formal reply).")

        # Memo 3: Cross-Department Memo PENDING HOD Endorsement (ICT Staff -> Works HOD)
        memo3, created3 = Message.objects.get_or_create(
            sender=u_staff_ict,
            recipient=u_hod_works,
            subject='Specification Review for Secretariat Solar Power Integration',
            defaults={
                'priority': 'CONFIDENTIAL',
                'status': 'pending_hod',
                'is_read': False,
                'body': (
                    "The Head of Department, Works & Infrastructure,\n\n"
                    "Following the joint technical walkthrough of the Secretariat complex, ICT has outlined the "
                    "power load calculations for the dedicated server room and communications mast.\n\n"
                    "We request your engineering team to verify structural load capacities on the roof canopy."
                )
            }
        )
        if created3:
            self.stdout.write("  + Created cross-department memo awaiting HOD ICT endorsement.")

        # Memo 4: Recalled / Withdrawn Memo
        memo4, created4 = Message.objects.get_or_create(
            sender=u_staff_works,
            recipient=u_hod_prc,
            subject='Requisition for Asphalt Premix - Ward 2 Resurfacing [WITHDRAWN]',
            defaults={
                'priority': 'ROUTINE',
                'status': 'recalled',
                'is_read': False,
                'recalled_at': timezone.now(),
                'recall_reason': 'Withdrawn due to updated bill of quantities and revised contractor metric rates.',
                'body': "Initial draft figures submitted in error. Please discard."
            }
        )
        if created4:
            self.stdout.write("  + Created sample withdrawn/recalled memorandum.")

        # -------------------------------------------------------------------
        # 4. Notice Board & Bulletin Items
        # -------------------------------------------------------------------
        notices_data = [
            {
                'title': 'Monthly Joint Departmental Review Meeting & Workplan Submission',
                'category': 'MEETING',
                'is_pinned': True,
                'content': (
                    "All Heads of Departments, Sectional Heads, and Administrative Officers are hereby notified that "
                    "the Monthly Joint Review Meeting for November 2026 will hold in the Council Executive Chamber "
                    "on Wednesday at 10:00 AM prompt.\n\n"
                    "All departments must submit their consolidated achievements and rolling workplans via the "
                    "Council Mailing System by Tuesday noon."
                ),
                'author': u_cm
            },
            {
                'title': 'Council Secretariat LAN Maintenance and Server Upgrade',
                'category': 'GENERAL',
                'is_pinned': False,
                'content': (
                    "The ICT Department will conduct scheduled maintenance on the core Secretariat network switches "
                    "and uninterruptible power units this Saturday between 1:00 PM and 5:00 PM. Officers are advised "
                    "to conclude critical digital correspondence before the maintenance window."
                ),
                'author': u_hod_ict
            },
            {
                'title': 'Mandatory Adoption of Official Digital Memorandums & Reference Numbers',
                'category': 'URGENT',
                'is_pinned': True,
                'content': (
                    "In furtherance of council digitalization and administrative security, all official correspondence "
                    "between council departments must strictly utilize the Council Workspace Mailing System.\n\n"
                    "Memos without system-generated reference codes and verified digital signatures will not be accepted "
                    "for payment processing or administrative action."
                ),
                'author': u_cm
            },
        ]

        for ndata in notices_data:
            item, n_created = NoticeBoardItem.objects.get_or_create(
                title=ndata['title'],
                defaults={
                    'category': ndata['category'],
                    'is_pinned': ndata['is_pinned'],
                    'content': ndata['content'],
                    'author': ndata['author']
                }
            )
            if n_created:
                self.stdout.write(f"  + Created bulletin notice: {ndata['title']}")

        self.stdout.write(self.style.SUCCESS("\nSeeding complete!"))
        self.stdout.write(self.style.SUCCESS(f"All seeded accounts configured with password: {password}"))
