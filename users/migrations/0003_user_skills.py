from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
        ("users", "0002_user_favorites"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="skills",
            field=models.ManyToManyField(
                blank=True,
                related_name="users",
                to="projects.skill",
            ),
        ),
    ]
