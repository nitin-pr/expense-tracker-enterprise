from django.db.models import TextChoices


class PaymentMethod(TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"
    UPI = "upi", "UPI"
    NET_BANKING = "net_banking", "Net Banking"
    OTHER = "other", "Other"
