from common.repositories import BaseRepository

from .models import Expense


class ExpenseRepository(BaseRepository[Expense]):
    model = Expense
    # No extra methods needed yet - search/filter/sort/pagination are US-016/017/018
    # (Sprint 3). BaseRepository's inherited CRUD covers US-014/015's full scope.
