# Generated by Django 3.0.6 on 2020-05-26 13:11

from django.db import migrations, models
import martor.models


class Migration(migrations.Migration):

    dependencies = [
        ("compare", "0007_auto_20200526_1300"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ocrupdate", name="text", field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="post",
            name="description",
            field=martor.models.MartorField(blank=True),
        ),
    ]
