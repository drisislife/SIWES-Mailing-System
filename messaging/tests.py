from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Department
from messaging.models import Message, MessageAcknowledgement

User = get_user_model()

class HODApprovalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.it_dept = Department.objects.create(name="IT Department")
        self.hr_dept = Department.objects.create(name="HR Department")

        # Staff in IT
        self.staff_it = User.objects.create_user(
            username="staff_it@org.com",
            email="staff_it@org.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            department=self.it_dept,
            role='STAFF',
            account_approved=True
        )

        # Staff in HR
        self.staff_hr = User.objects.create_user(
            username="staff_hr@org.com",
            email="staff_hr@org.com",
            password="password123",
            first_name="Jane",
            last_name="Smith",
            department=self.hr_dept,
            role='STAFF',
            account_approved=True
        )

        # HOD of IT
        self.hod_it = User.objects.create_user(
            username="hod_it@org.com",
            email="hod_it@org.com",
            password="password123",
            first_name="Boss",
            last_name="Chief",
            department=self.it_dept,
            role='HOD',
            account_approved=True
        )

        # Admin / Superuser
        self.admin_user = User.objects.create_superuser(
            username="admin@org.com",
            email="admin@org.com",
            password="password123",
            first_name="Admin",
            last_name="Super"
        )

    def test_message_detail_records_read_receipt(self):
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Confidential Memo',
            body='Please review carefully.',
            status='approved',
            is_read=False
        )
        self.assertIsNone(msg.read_at)

        # Recipient reads message
        self.client.login(username="staff_hr@org.com", password="password123")
        response = self.client.get(reverse('message_detail', kwargs={'pk': msg.id}))
        self.assertEqual(response.status_code, 200)

        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
        self.assertIsNotNone(msg.read_at)

    def test_recipient_can_acknowledge_receipt(self):
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Action Required Memo',
            body='Please take action immediately.',
            status='approved'
        )

        self.client.login(username="staff_hr@org.com", password="password123")
        response = self.client.post(
            reverse('message_detail', kwargs={'pk': msg.id}),
            {'action': 'acknowledge', 'note': 'Received and action in progress.'}
        )
        self.assertEqual(response.status_code, 302)

        ack = MessageAcknowledgement.objects.filter(message=msg).first()
        self.assertIsNotNone(ack)
        self.assertEqual(ack.acknowledged_by, self.staff_hr)
        self.assertEqual(ack.note, 'Received and action in progress.')

    def test_reply_threading(self):
        parent_msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Initial Council Proposal',
            body='Here is our initial proposal.',
            status='approved'
        )

        # Compose reply from HR back to IT
        self.client.login(username="staff_hr@org.com", password="password123")
        response = self.client.post(
            f"{reverse('compose_message')}?parent={parent_msg.id}",
            {
                'recipient': self.staff_it.id,
                'priority': 'ROUTINE',
                'subject': 'Re: Initial Council Proposal',
                'body': 'We accept the proposal with adjustments.'
            }
        )
        self.assertEqual(response.status_code, 302)

        reply = Message.objects.get(subject='Re: Initial Council Proposal')
        self.assertEqual(reply.parent, parent_msg)
        self.assertEqual(parent_msg.replies.first(), reply)
