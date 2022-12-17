from django.contrib import admin

# Register your models here.
from .models import Submission, Moderation, RepSecret, Group

admin.site.register(Submission)
admin.site.register(Moderation)
admin.site.register(RepSecret)
admin.site.register(Group)