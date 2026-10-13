from common.services import BaseService
from common.utils import month_bounds
from common.validators import validate_positive_amount


class IncomeService(BaseService):
    def create_income(self, user, source, amount, income_date):
        validate_positive_amount(amount)
        return self.repository.create(user=user, source=source, amount=amount, income_date=income_date)

    def update_income(self, income, **data):
        if "amount" in data:
            validate_positive_amount(data["amount"])
        return self.repository.update(income, **data)

    def delete_income(self, income):
        self.repository.delete(income)

    def get_income(self, income_id):
        return self.repository.get_by_id(income_id)

    def get_monthly_total(self, user, month, year):
        date_from, date_to = month_bounds(year, month)
        return self.repository.sum_for_period(user, date_from, date_to)
