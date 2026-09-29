from django.db import models


class User(models.Model):
    firebase_uid = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True)
    photo = models.URLField(max_length=500, blank=True, null=True)
    currency = models.CharField(max_length=3, default="INR")
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    theme = models.CharField(
        max_length=10,
        default="light",
        choices=[("light", "Light"), ("dark", "Dark")],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(theme__in=["light", "dark"]),
                name="user_theme_valid",
            )
        ]

    @property
    def is_authenticated(self):
        # DRF's IsAuthenticated permission checks this attribute, which normally
        # comes from Django's AbstractBaseUser. Since this User doesn't inherit
        # from that, it's supplied explicitly: any resolved User instance IS
        # authenticated by definition - FirebaseAuthentication never returns one
        # otherwise (it returns None instead, which DRF treats as AnonymousUser).
        return True

    def __str__(self):
        return self.email
