# Generated manually for secure_computation app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('requests_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecureComputationValidation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zkp_verified', models.BooleanField(default=False)),
                ('tee_verified', models.BooleanField(default=False)),
                ('smpc_verified', models.BooleanField(default=False)),
                ('overall_verified', models.BooleanField(default=False)),
                ('zkp_proof', models.JSONField(blank=True, null=True)),
                ('tee_attestation', models.JSONField(blank=True, null=True)),
                ('smpc_result', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('validated_at', models.DateTimeField(blank=True, null=True)),
                ('request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='secure_validation', to='requests_app.dataaccessrequest')),
            ],
        ),
    ]
