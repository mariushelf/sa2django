from django.db import models


class Parent(models.Model):
    class Meta:
        managed = False
        db_table = "parent"

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
