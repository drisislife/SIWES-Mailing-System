from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, Department
from messaging.models import Message

class HODApprovalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.it_dept = Department.objects.create(name="IT Department")
        self.hr_dept = Department.objects.create(name="HR Department")

        # Staff in IT
        self.staff_it = User.objects.create_user(
            username="staff_it",
            email="staff_it@org.com",
            password="password123",
            department=self.it_dept,
            role=User.Role.STAFF,
            email_verified=True,
            account_approved=True
        )

        # Staff in HR
        self.staff_hr = User.objects.create_user(
            username="staff_hr",
            email="staff_hr@org.com",
            password="password123",
            department=self.hr_dept,
            role=User.Role.STAFF,
            email_verified=True,
            account_approved=True
        )

        # HOD of IT
        self.hod_it = User.objects.create_user(
            username="hod_it",
            email="hod_it@org.com",
            password="password123",
            department=self.it_dept,
            role=User.Role.HOD,
            email_verified=True,
            account_approved=True
        )

        # Admin / Superuser
        self.admin_user = User.objects.create_superuser(
            username="superadmin",
            email="admin@org.com",
            password="password123"
        )

    def test_staff_cannot_access_approvals_portal(self):
        self.client.login(username="staff_it@org.com", password="password123")
        response = self.client.get(reverse('hod_approvals'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('inbox'))

    def test_cross_dept_message_triggers_pending_hod(self):
        self.client.login(username="staff_it@org.com", password="password123")
        response = self.client.post(reverse('compose_message'), {
            'recipient': self.staff_hr.id,
            'subject': 'IT Support needed for HR',
            'body': 'Please check network cables.'
        })
        self.assertEqual(response.status_code, 302)
        msg = Message.objects.get(subject='IT Support needed for HR')
        self.assertEqual(msg.status, 'pending_hod')

    def test_hod_approves_outgoing_message(self):
        # Create pending message from IT to HR
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Cross Department Request',
            body='Hello HR',
            status='pending_hod'
        )

        # Log in as IT HOD
        self.client.login(username="hod_it@org.com", password="password123")
        response = self.client.get(reverse('hod_approvals'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cross Department Request')

        # Approve the message
        approve_response = self.client.post(
            reverse('approve_message', kwargs={'message_id': msg.id}),
            {'hod_comment': 'Approved by IT HOD'}
        )
        self.assertEqual(approve_response.status_code, 302)
        msg.refresh_from_db()
        self.assertEqual(msg.status, 'approved')
        self.assertEqual(msg.hod_comment, 'Approved by IT HOD')

    def test_hod_rejects_message(self):
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Budget Transfer',
            body='Requesting budget',
            status='pending_hod'
        )

        self.client.login(username="hod_it@org.com", password="password123")
        reject_response = self.client.post(
            reverse('reject_message', kwargs={'message_id': msg.id}),
            {'hod_comment': 'Budget request invalid'}
        )
        self.assertEqual(reject_response.status_code, 302)
        msg.refresh_from_db()
        self.assertEqual(msg.status, 'rejected')
        self.assertEqual(msg.hod_comment, 'Budget request invalid')

    def test_admin_can_view_and_approve_all(self):
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Admin Review Needed',
            body='Some content',
            status='pending_hod'
        )

        self.client.login(username="admin@org.com", password="password123")
        response = self.client.get(reverse('hod_approvals'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Review Needed')

    def test_sent_messages_view(self):
        Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='My Sent Item',
            body='Body of sent item',
            status='approved'
        )
        self.client.login(username="staff_it@org.com", password="password123")
        response = self.client.get(reverse('sent_messages'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Sent Item')

    def test_message_detail_marks_as_read_for_recipient(self):
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Confidential Memo',
            body='Please review carefully.',
            status='approved',
            is_read=False
        )

        # Recipient reads message
        self.client.login(username="staff_hr@org.com", password="password123")
        response = self.client.get(reverse('message_detail', kwargs={'message_id': msg.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please review carefully.')

        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_unauthorized_user_cannot_read_message(self):
        # Third user
        other_user = User.objects.create_user(
            username="intruder",
            email="intruder@org.com",
            password="password123",
            department=self.it_dept,
            role=User.Role.STAFF
        )
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Private Discussion',
            body='Secret content',
            status='approved'
        )

        self.client.login(username="intruder@org.com", password="password123")
        response = self.client.get(reverse('message_detail', kwargs={'message_id': msg.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('inbox'))

    def test_hod_review_and_edit_message(self):
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Initial Draft Subject',
            body='Original draft body with typos.',
            status='pending_hod'
        )

        self.client.login(username="hod_it@org.com", password="password123")
        
        # 1. Access review page
        review_response = self.client.get(reverse('hod_review_message', kwargs={'message_id': msg.id}))
        self.assertEqual(review_response.status_code, 200)
        self.assertContains(review_response, 'Initial Draft Subject')
        self.assertContains(review_response, 'Original draft body with typos.')

        # 2. Submit edit and approve
        approve_response = self.client.post(
            reverse('approve_message', kwargs={'message_id': msg.id}),
            {
                'subject': 'Polished Official Subject',
                'body': 'Corrected professional body without typos.',
                'hod_comment': 'Proofread and refined by HOD.'
            }
        )
        self.assertEqual(approve_response.status_code, 302)

        msg.refresh_from_db()
        self.assertEqual(msg.status, 'approved')
        self.assertEqual(msg.subject, 'Polished Official Subject')
        self.assertEqual(msg.body, 'Corrected professional body without typos.')
        self.assertEqual(msg.original_body, 'Original draft body with typos.')
        self.assertTrue(msg.edited_by_hod)
        self.assertEqual(msg.hod_comment, 'Proofread and refined by HOD.')

        # 3. Recipient views the edited message and sees the HOD badge
        self.client.login(username="staff_hr@org.com", password="password123")
        detail_response = self.client.get(reverse('message_detail', kwargs={'message_id': msg.id}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Polished Official Subject')
        self.assertContains(detail_response, 'Edited by HOD')
        self.assertContains(detail_response, 'Proofread and refined by HOD.')

    def test_toggle_message_read(self):
        msg = Message.objects.create(
            sender=self.staff_it,
            recipient=self.staff_hr,
            subject='Toggle Read Test',
            body='Some body',
            status='approved',
            is_read=True
        )

        self.client.login(username="staff_hr@org.com", password="password123")
        response = self.client.post(reverse('toggle_message_read', kwargs={'message_id': msg.id}))
        self.assertEqual(response.status_code, 302)

        msg.refresh_from_db()
        self.assertFalse(msg.is_read)
