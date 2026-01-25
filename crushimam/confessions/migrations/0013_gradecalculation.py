# Generated migration for updated GradeCalculation model with exams and coefficients

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('confessions', '0012_partner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GradeCalculation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('5eme', '5ème année'), ('1bac', '1ère année BAC'), ('2bac', '2ème année BAC')], max_length=10)),
                ('branch', models.CharField(blank=True, max_length=50)),
                ('subjects_data', models.JSONField(default=dict, help_text='{"Subject": {"exams": [15, 16, 14], "behavior": 18, "coefficient": 3}}')),
                ('calculated_average', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grade_calculations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Grade Calculation',
                'verbose_name_plural': 'Grade Calculations',
                'ordering': ['-created_at'],
            },
        ),
    ]

