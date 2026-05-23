import uuid

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS postgis;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.CreateModel(
            name="Zone",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="name")),
                (
                    "zone_type",
                    models.CharField(
                        choices=[
                            ("parking_allowed", "Parking Allowed"),
                            ("no_parking", "No Parking"),
                            ("speed_limited", "Speed Limited"),
                            ("forbidden", "Forbidden"),
                        ],
                        max_length=20,
                        verbose_name="zone type",
                    ),
                ),
                (
                    "geometry",
                    django.contrib.gis.db.models.fields.PolygonField(
                        srid=4326, verbose_name="geometry"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="active"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "zone",
                "verbose_name_plural": "zones",
                "ordering": ["-created_at"],
            },
        ),
    ]
