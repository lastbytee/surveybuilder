from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser , BaseUserManager
from datetime import datetime
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and returns a regular user with an email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and returns a superuser with an email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True)  # You can leave this blank since we use email as the username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Make sure this is empty or contains fields you want to prompt the user for

    objects = CustomUserManager()

    def __str__(self):
        return self.email
 
class Survey(models.Model):
    PROVINCE_CHOICES = [
        ('Kigali', 'Kigali'),
        ('Eastern', 'Eastern'),
        ('Western', 'Western'),
        ('Northern', 'Northern'),
        ('Southern', 'Southern'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=20, choices=PROVINCE_CHOICES, blank=True ,null=True) 

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('rating', 'Rating'),
        ('yesno', 'Yes/No'),
        ('dropdown', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio'),
        ('date', 'Date'),
    ]
    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    required = models.BooleanField(default=False)
    options = models.TextField(blank=True, help_text='Comma-separated options for choice-based questions')

    def __str__(self):
        return self.label

class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to '{self.survey.title}' at {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"


class Answer(models.Model):
    response = models.ForeignKey(Response, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True)


    def __str__(self):
        return f"Answer to {self.question.label}"
    

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return f'Message from {self.name}'
