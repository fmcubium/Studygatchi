from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class StudyUser(User):
    # inherits: username, password, email, ...
    money = models.IntegerField(default=100)

# class Task(models.Model):
#     # task_id will be automatically created by Django
#     reward = models.IntegerField(default=0)
#     name = models.TextField(default="task")
#     category = models.TextField(null=True)
#     due_date = models.DateTimeField()
#     description = models.TextField()
#     username = models.ForeignKey(StudyUser, on_delete=models.CASCADE)

class Pet(models.Model):
    # ID automatically created by Django
    type = models.TextField(default="pet")
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    happiness = models.DecimalField(default=0.5)
    equipped_clothes = models.IntegerField(null=True)
    image_url = models.URLField(null=True) # Change in the future
    owner = models.ForeignKey(StudyUser, on_delete=models.CASCADE)
