# Generated by Django 2.2.6 on 2021-05-13 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0014_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(help_text='Введите текст комментария', verbose_name='Комментарий'),
        ),
    ]
