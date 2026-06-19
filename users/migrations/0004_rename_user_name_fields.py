from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_user_skills"),
    ]

    operations = [
        migrations.RenameField(
            model_name="user",
            old_name="name",
            new_name="first_name",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="surname",
            new_name="last_name",
        ),
    ]
