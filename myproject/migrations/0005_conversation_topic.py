# Generated by Django 4.2.16 on 2024-10-23 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myproject', '0004_merge_0003_conversation_message_0003_userfile_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='topic',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]