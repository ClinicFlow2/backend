from django.db import migrations


def fill_patient_codes(apps, schema_editor):
    Patient = apps.get_model("patients", "Patient")

    for p in Patient.objects.all().only("id", "patient_code"):
        if not p.patient_code:
            p.patient_code = f"PT-{p.id:06d}"
            p.save(update_fields=["patient_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("patients", "0004_alter_patient_patient_code"),
    ]

    operations = [
        migrations.RunPython(fill_patient_codes, migrations.RunPython.noop),
    ]
