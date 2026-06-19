from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0005_alter_user_options_alter_user_about_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="user",
            old_name="first_name",
            new_name="name",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="last_name",
            new_name="surname",
        ),
    ]
