from common.exceptions import ValidationError
from common.services import BaseService
from common.validators import validate_not_future_date, validate_positive_amount


class ExpenseService(BaseService):
    def _validate_category_access(self, user, category):
        if category.created_by_id not in (None, user.id):
            raise ValidationError("You can only use your own categories or default categories.")

    def create_expense(
        self, user, category, title, amount, payment_method, expense_date,
        description="", notes="", attachment=None,
    ):
        self._validate_category_access(user, category)
        validate_positive_amount(amount)
        validate_not_future_date(expense_date)
        return self.repository.create(
            user=user,
            category=category,
            title=title,
            amount=amount,
            payment_method=payment_method,
            expense_date=expense_date,
            description=description,
            notes=notes,
            attachment=attachment,
        )

    def update_expense(self, user, expense, **data):
        if "category" in data:
            self._validate_category_access(user, data["category"])
        if "amount" in data:
            validate_positive_amount(data["amount"])
        if "expense_date" in data:
            validate_not_future_date(data["expense_date"])
        return self.repository.update(expense, **data)

    def delete_expense(self, expense):
        self.repository.delete(expense)

    def get_expense(self, expense_id):
        return self.repository.get_by_id(expense_id)
