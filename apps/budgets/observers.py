from abc import ABC, abstractmethod


class BudgetObserver(ABC):
    """
    Real ABC, same reasoning as AuthProvider: there's no sensible default for
    "react to a budget crossing a threshold" - every observer has to actually
    implement something. Decouples "a budget crossed a threshold" (BudgetService's
    concern) from "who needs to react and how" (NotificationService's concern,
    today; could be others later without BudgetService ever changing).
    """

    @abstractmethod
    def on_threshold_crossed(self, user, budget, spent, percent, threshold_tier):
        ...
