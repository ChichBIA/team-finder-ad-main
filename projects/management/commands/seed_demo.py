from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project, Skill
from users.models import User


class Command(BaseCommand):
    help = "Create demo users, projects, and skills"

    def handle(self, *args, **options):
        users_data = [
            ("alina@example.com", "Alina", "Ivanova"),
            ("andrey@example.com", "Andrey", "Smirnov"),
            ("alena@example.com", "Alena", "Sidorova"),
        ]
        skills_data = ["Django", "PostgreSQL", "Docker", "JavaScript"]

        with transaction.atomic():
            skills = [Skill.objects.get_or_create(name=name)[0] for name in skills_data]

            users = []
            for email, name, surname in users_data:
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={"name": name, "surname": surname},
                )
                if created:
                    user.set_password("demo12345")
                    user.save()
                users.append(user)

            for idx, user in enumerate(users, start=1):
                project, created = Project.objects.get_or_create(
                    name=f"Demo Project {idx}",
                    defaults={
                        "description": "Sample project created for demo purposes.",
                        "owner": user,
                        "status": Project.Status.OPEN,
                    },
                )
                if created:
                    project.participants.add(user)
                    project.skills.add(skills[idx % len(skills)])

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
