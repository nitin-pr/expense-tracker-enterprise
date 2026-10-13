from django.db.models import TextChoices


class IncomeSource(TextChoices):
    SALARY = "salary", "Salary"
    FREELANCING = "freelancing", "Freelancing"
    INVESTMENT = "investment", "Investment"
    BONUS = "bonus", "Bonus"
    OTHER = "other", "Other"
