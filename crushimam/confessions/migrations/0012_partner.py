# Generated migration for Partner model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('confessions', '0011_activationcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='partners/')),
                ('website', models.URLField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('tier', models.CharField(choices=[('gold', 'Gold Partner'), ('silver', 'Silver Partner'), ('bronze', 'Bronze Partner'), ('sponsor', 'Sponsor')], default='sponsor', max_length=20)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Partner',
                'verbose_name_plural': 'Partners',
                'ordering': ['tier', 'order', '-created_at'],
            },
        ),
    ]
