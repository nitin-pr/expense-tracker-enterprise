from rest_framework.permissions import BasePermission


class IsCategoryOwner(BasePermission):
    """
    common.permissions.IsOwner checks obj.user_id, which fits Expense/Income/Budget
    (all use a `user` FK per DATABASE_DESIGN.md) but not Category, which
    deliberately uses `created_by` instead (a more precise name for "who created
    this category" than a generic owner field). Kept local to this app since it's
    specific to this one model's field name, not a reusable cross-cutting utility.

    Also correctly denies permission for default categories (created_by=None),
    since None never equals a real user id - satisfies "default categories
    cannot be edited/deleted by any user" without extra special-casing.
    """

    def has_object_permission(self, request, view, obj):
        return obj.created_by_id == request.user.id
