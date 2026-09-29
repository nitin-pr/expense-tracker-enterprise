from django.db import migrations

DEFAULT_CATEGORIES = [
    {"name": "Food", "icon": "cart3", "color": "#FF6B6B"},
    {"name": "Travel", "icon": "airplane", "color": "#4ECDC4"},
    {"name": "Bills", "icon": "receipt", "color": "#FFD93D"},
    {"name": "Entertainment", "icon": "film", "color": "#A78BFA"},
    {"name": "Medical", "icon": "heart-pulse", "color": "#F87171"},
    {"name": "Education", "icon": "book", "color": "#60A5FA"},
    {"name": "Shopping", "icon": "bag", "color": "#F472B6"},
    {"name": "Investment", "icon": "graph-up-arrow", "color": "#34D399"},
    {"name": "Salary", "icon": "cash-stack", "color": "#10B981"},
    {"name": "Other", "icon": "three-dots", "color": "#9CA3AF"},
]


def seed_default_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    for entry in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            created_by=None,
            name=entry["name"],
            defaults={"icon": entry["icon"], "color": entry["color"]},
        )


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    names = [entry["name"] for entry in DEFAULT_CATEGORIES]
    Category.objects.filter(created_by__isnull=True, name__in=names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, remove_default_categories),
    ]
