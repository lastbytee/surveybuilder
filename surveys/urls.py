from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('mysurvey/', mysurvey, name = 'mysurvey'),
    path('create/', create_survey, name='create_survey'),
    path('take/<int:pk>/', take_survey, name='take_survey'),
    path('thank-you/', thank_you, name='thank_you'),
    path('logout/', logout, name='logout'),
    path('responses/<int:survey_id>/', view_responses, name='view_responses'),
    path('survey/<int:survey_id>/export/', export_to_excel, name='export_to_excel'),
    path('survey/<int:pk>/delete/', delete_survey, name='delete_survey'),
    path('login/', login, name='login'),
    path('signup/', signup, name='signup'),
    path('survey/<int:survey_id>/edit/', edit_survey, name='edit_survey'),
    path('about/', about, name = 'about'),
    path('contact/', contact, name = 'contact'),
    path('template/',survey_template, name='survey_template'),





]

