from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Survey)
admin.site.register(Question)
admin.site.register(Response)
admin.site.register(Answer)
admin.site.register(Contact)


