from django.test import TestCase
from .models import Group

# Create your tests here.
class MyTestCase(TestCase):

	def test_tests(self):
		self.assertIs(True, True)

	def test_db_access(self):
		group = Group.objects.get(pk='Test1')
		self.assertIs(group.name == 'Test1', True)

	def test_db_changes(self):
		for g in Group.objects.all():
			g.status = 'RED'
			g.save()
		for g in Group.objects.all():
			self.assertIs(g.status == 'RED', True)
	
	# Test all basic functionalities

	# test for landing page

	# test for landing on all group pages

	# test for checking rep-secret

	# test for going to comment page

	# test for making submission

	# test for moderating submission

	# test for rejecting submission

	# test for accepting submission

	# test for publishing to facebook page

	# test for publishing to instagram

	# test for publishing to google form

	# test for submitting comment

	# test for submitting reply
	