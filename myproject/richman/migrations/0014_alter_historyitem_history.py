# Generated by Django 5.1.4 on 2025-02-11 09:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('richman', '0013_historyitem_history_alter_history_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historyitem',
            name='history',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='history_items', to='richman.history'),
            preserve_default=False,
        ),
    ]
