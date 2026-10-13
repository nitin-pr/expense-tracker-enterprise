import { requireToken, apiFetch, apiGet, apiJson, logout } from "./api.js";

requireToken(); // redirects to /login/ immediately if there's no token - nothing below should run otherwise

document.getElementById("logout-btn").addEventListener("click", logout);

let categories = [];
let expensesNextUrl = null;
let expensesPrevUrl = null;
let editingIncomeId = null;
let editingExpenseId = null;

function money(value) {
    return `₹${Number(value).toFixed(2)}`;
}

function capitalize(value) {
    return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatPaymentMethod(value) {
    return { cash: "Cash", card: "Card", upi: "UPI", net_banking: "Net Banking", other: "Other" }[value] || value;
}

function showPageError(message) {
    const box = document.getElementById("page-error");
    box.textContent = message;
    box.classList.remove("d-none");
    setTimeout(() => box.classList.add("d-none"), 5000);
}

function formatApiError(data) {
    // Two different error shapes depending on where a 400 originated:
    // - our own ValidationError (service-layer rules) -> {code, message, details}
    // - DRF's own serializer validation (missing/invalid field, before our
    //   service layer ever runs) -> {field_name: ["error", ...], ...}
    if (!data) return "Something went wrong.";
    if (data.message) return data.message;
    const parts = Object.entries(data).map(
        ([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(" ") : messages}`
    );
    return parts.join(" ") || "Something went wrong.";
}

function debounce(fn, delayMs) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delayMs);
    };
}

function modalFor(id) {
    return bootstrap.Modal.getOrCreateInstance(document.getElementById(id));
}

// ---------------------------------------------------------------- Summary

async function loadSummary() {
    const data = await apiGet("/api/dashboard/");
    if (!data) return;
    document.getElementById("summary-today-expense").textContent = money(data.today_expense);
    document.getElementById("summary-monthly-expense").textContent = money(data.monthly_expense);
    document.getElementById("summary-monthly-income").textContent = money(data.monthly_income);
    document.getElementById("summary-remaining-budget").textContent =
        data.remaining_budget === null ? "Not set" : money(data.remaining_budget);
    document.getElementById("summary-total-categories").textContent = data.total_categories;
}

// ---------------------------------------------------------------- Budget

async function loadBudget() {
    const today = new Date();
    const response = await apiFetch(`/api/budgets/?month=${today.getMonth() + 1}&year=${today.getFullYear()}`);
    if (!response) return;

    if (response.status === 404) {
        document.getElementById("budget-no-budget").classList.remove("d-none");
        document.getElementById("budget-details").classList.add("d-none");
        return;
    }

    const data = await response.json();
    document.getElementById("budget-no-budget").classList.add("d-none");
    document.getElementById("budget-details").classList.remove("d-none");

    const percent = data.percent_used;
    const bar = document.getElementById("budget-progress-bar");
    bar.style.width = `${Math.min(percent, 100)}%`;
    bar.textContent = `${percent}%`;
    bar.className = "progress-bar " + (percent >= 90 ? "bg-danger" : percent >= 80 ? "bg-warning" : "bg-success");

    document.getElementById("budget-spent-text").textContent = `Spent: ${money(data.spent)}`;
    document.getElementById("budget-total-text").textContent = `Budget: ${money(data.budget)}`;
}

document.getElementById("budget-modal").addEventListener("show.bs.modal", () => {
    const today = new Date();
    document.getElementById("budget-month").value = today.getMonth() + 1;
    document.getElementById("budget-year").value = today.getFullYear();
});

document.getElementById("budget-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = document.getElementById("budget-form-error");
    errorBox.classList.add("d-none");

    const payload = {
        month: Number(document.getElementById("budget-month").value),
        year: Number(document.getElementById("budget-year").value),
        budget: document.getElementById("budget-amount").value,
    };
    const { ok, data } = await apiJson("/api/budgets/", "POST", payload);

    if (!ok) {
        errorBox.textContent = formatApiError(data);
        errorBox.classList.remove("d-none");
        return;
    }
    modalFor("budget-modal").hide();
    document.getElementById("budget-form").reset();
    await Promise.all([loadBudget(), loadSummary()]);
});

// ---------------------------------------------------------------- Categories

async function loadCategories() {
    const data = await apiGet("/api/categories/");
    if (!data) return;
    categories = data;

    const list = document.getElementById("categories-list");
    list.innerHTML = "";
    data.forEach((category) => {
        const badge = document.createElement("span");
        badge.className = "badge rounded-pill d-inline-flex align-items-center gap-2 p-2";
        badge.style.backgroundColor = category.color;
        badge.style.color = "#fff";
        badge.innerHTML = `<i class="bi bi-${category.icon}"></i> ${category.name}`;

        if (category.created_by) {
            const deleteBtn = document.createElement("button");
            deleteBtn.type = "button";
            deleteBtn.className = "btn-close btn-close-white";
            deleteBtn.style.fontSize = "0.55rem";
            deleteBtn.setAttribute("aria-label", `Delete ${category.name}`);
            deleteBtn.addEventListener("click", () => deleteCategory(category.id));
            badge.appendChild(deleteBtn);
        }
        list.appendChild(badge);
    });

    const filterSelect = document.getElementById("filter-category");
    const formSelect = document.getElementById("expense-category");
    const previousFilterValue = filterSelect.value;
    filterSelect.innerHTML = '<option value="">All categories</option>';
    formSelect.innerHTML = "";
    data.forEach((category) => {
        filterSelect.insertAdjacentHTML("beforeend", `<option value="${category.id}">${category.name}</option>`);
        formSelect.insertAdjacentHTML("beforeend", `<option value="${category.id}">${category.name}</option>`);
    });
    filterSelect.value = previousFilterValue;
}

async function deleteCategory(id) {
    const { ok, data } = await apiJson(`/api/categories/${id}/`, "DELETE");
    if (!ok) {
        // Expected failure case, not an edge case: deleting a category still
        // referenced by an expense returns a clean 400 (US-013) - surfaced
        // here rather than silently ignored.
        showPageError(formatApiError(data));
        return;
    }
    await Promise.all([loadCategories(), loadSummary()]);
}

document.getElementById("category-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = document.getElementById("category-form-error");
    errorBox.classList.add("d-none");

    const payload = {
        name: document.getElementById("category-name").value,
        icon: document.getElementById("category-icon").value,
        color: document.getElementById("category-color").value,
    };
    const { ok, data } = await apiJson("/api/categories/", "POST", payload);

    if (!ok) {
        errorBox.textContent = formatApiError(data);
        errorBox.classList.remove("d-none");
        return;
    }
    modalFor("category-modal").hide();
    document.getElementById("category-form").reset();
    await Promise.all([loadCategories(), loadSummary()]);
});

// ---------------------------------------------------------------- Income

async function loadIncome() {
    const data = await apiGet("/api/income/");
    if (!data) return;

    const tbody = document.getElementById("income-table-body");
    const empty = document.getElementById("income-empty");
    tbody.innerHTML = "";
    empty.classList.toggle("d-none", data.length > 0);

    data.forEach((entry) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${capitalize(entry.source)}</td>
            <td>${money(entry.amount)}</td>
            <td>${entry.income_date}</td>
            <td class="text-end">
                <button type="button" class="btn btn-sm btn-outline-secondary edit-income-btn" data-id="${entry.id}">Edit</button>
                <button type="button" class="btn btn-sm btn-outline-danger delete-income-btn" data-id="${entry.id}">Delete</button>
            </td>`;
        tbody.appendChild(row);
    });

    tbody.querySelectorAll(".edit-income-btn").forEach((btn) =>
        btn.addEventListener("click", () => openIncomeModalForEdit(data.find((e) => e.id === Number(btn.dataset.id))))
    );
    tbody.querySelectorAll(".delete-income-btn").forEach((btn) =>
        btn.addEventListener("click", () => deleteIncome(Number(btn.dataset.id)))
    );
}

function openIncomeModalForEdit(entry) {
    editingIncomeId = entry.id;
    document.getElementById("income-modal-title").textContent = "Edit Income";
    document.getElementById("income-id").value = entry.id;
    document.getElementById("income-source").value = entry.source;
    document.getElementById("income-amount").value = entry.amount;
    document.getElementById("income-date").value = entry.income_date;
    modalFor("income-modal").show();
}

document.getElementById("add-income-btn").addEventListener("click", () => {
    editingIncomeId = null;
    document.getElementById("income-modal-title").textContent = "Add Income";
    document.getElementById("income-form").reset();
});

async function deleteIncome(id) {
    const { ok, data } = await apiJson(`/api/income/${id}/`, "DELETE");
    if (!ok) {
        showPageError(formatApiError(data));
        return;
    }
    await Promise.all([loadIncome(), loadSummary()]);
}

document.getElementById("income-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = document.getElementById("income-form-error");
    errorBox.classList.add("d-none");

    const payload = {
        source: document.getElementById("income-source").value,
        amount: document.getElementById("income-amount").value,
        income_date: document.getElementById("income-date").value,
    };
    const path = editingIncomeId ? `/api/income/${editingIncomeId}/` : "/api/income/";
    const method = editingIncomeId ? "PUT" : "POST";
    const { ok, data } = await apiJson(path, method, payload);

    if (!ok) {
        errorBox.textContent = formatApiError(data);
        errorBox.classList.remove("d-none");
        return;
    }
    modalFor("income-modal").hide();
    document.getElementById("income-form").reset();
    await Promise.all([loadIncome(), loadSummary()]);
});

// ---------------------------------------------------------------- Expenses

function buildExpensesUrl() {
    const params = new URLSearchParams();
    const search = document.getElementById("filter-search").value;
    const category = document.getElementById("filter-category").value;
    const paymentMethod = document.getElementById("filter-payment-method").value;
    const dateFrom = document.getElementById("filter-date-from").value;
    const dateTo = document.getElementById("filter-date-to").value;
    const ordering = document.getElementById("filter-ordering").value;

    if (search) params.set("search", search);
    if (category) params.set("category", category);
    if (paymentMethod) params.set("payment_method", paymentMethod);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    if (ordering) params.set("ordering", ordering);

    return `/api/expenses/?${params.toString()}`;
}

async function loadExpenses(url = null) {
    const response = await apiFetch(url || buildExpensesUrl());
    if (!response) return;
    const data = await response.json();

    if (!response.ok) {
        showPageError(formatApiError(data));
        return;
    }

    expensesNextUrl = data.next;
    expensesPrevUrl = data.previous;

    const tbody = document.getElementById("expenses-table-body");
    const empty = document.getElementById("expenses-empty");
    tbody.innerHTML = "";
    empty.classList.toggle("d-none", data.results.length > 0);

    data.results.forEach((expense) => {
        const category = categories.find((c) => c.id === expense.category);
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${expense.title}</td>
            <td>${money(expense.amount)}</td>
            <td>${category ? category.name : "-"}</td>
            <td>${formatPaymentMethod(expense.payment_method)}</td>
            <td>${expense.expense_date}</td>
            <td class="text-end">
                <button type="button" class="btn btn-sm btn-outline-secondary edit-expense-btn" data-id="${expense.id}">Edit</button>
                <button type="button" class="btn btn-sm btn-outline-danger delete-expense-btn" data-id="${expense.id}">Delete</button>
            </td>`;
        tbody.appendChild(row);
    });

    tbody.querySelectorAll(".edit-expense-btn").forEach((btn) =>
        btn.addEventListener("click", () => openExpenseModalForEdit(data.results.find((e) => e.id === Number(btn.dataset.id))))
    );
    tbody.querySelectorAll(".delete-expense-btn").forEach((btn) =>
        btn.addEventListener("click", () => deleteExpense(Number(btn.dataset.id)))
    );

    document.getElementById("expenses-prev").disabled = !expensesPrevUrl;
    document.getElementById("expenses-next").disabled = !expensesNextUrl;
    document.getElementById("expenses-page-info").textContent = `${data.results.length} of ${data.count}`;
}

document.getElementById("expenses-prev").addEventListener("click", () => expensesPrevUrl && loadExpenses(expensesPrevUrl));
document.getElementById("expenses-next").addEventListener("click", () => expensesNextUrl && loadExpenses(expensesNextUrl));

document.getElementById("filter-search").addEventListener("input", debounce(() => loadExpenses(), 400));
["filter-category", "filter-payment-method", "filter-date-from", "filter-date-to", "filter-ordering"].forEach((id) => {
    document.getElementById(id).addEventListener("change", () => loadExpenses());
});

function openExpenseModalForEdit(expense) {
    editingExpenseId = expense.id;
    document.getElementById("expense-modal-title").textContent = "Edit Expense";
    document.getElementById("expense-id").value = expense.id;
    document.getElementById("expense-title").value = expense.title;
    document.getElementById("expense-amount").value = expense.amount;
    document.getElementById("expense-category").value = expense.category;
    document.getElementById("expense-payment-method").value = expense.payment_method;
    document.getElementById("expense-date").value = expense.expense_date;
    document.getElementById("expense-description").value = expense.description || "";
    document.getElementById("expense-notes").value = expense.notes || "";
    modalFor("expense-modal").show();
}

document.getElementById("add-expense-btn").addEventListener("click", () => {
    editingExpenseId = null;
    document.getElementById("expense-modal-title").textContent = "Add Expense";
    document.getElementById("expense-form").reset();
});

async function deleteExpense(id) {
    const { ok, data } = await apiJson(`/api/expenses/${id}/`, "DELETE");
    if (!ok) {
        showPageError(formatApiError(data));
        return;
    }
    // An expense change can affect budget spend/threshold and the summary -
    // refresh everything it could have touched, not just the list itself.
    await Promise.all([loadExpenses(), loadSummary(), loadBudget(), loadNotifications()]);
}

document.getElementById("expense-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = document.getElementById("expense-form-error");
    errorBox.classList.add("d-none");

    const payload = {
        title: document.getElementById("expense-title").value,
        amount: document.getElementById("expense-amount").value,
        category: Number(document.getElementById("expense-category").value),
        payment_method: document.getElementById("expense-payment-method").value,
        expense_date: document.getElementById("expense-date").value,
        description: document.getElementById("expense-description").value,
        notes: document.getElementById("expense-notes").value,
    };
    const path = editingExpenseId ? `/api/expenses/${editingExpenseId}/` : "/api/expenses/";
    const method = editingExpenseId ? "PUT" : "POST";
    const { ok, data } = await apiJson(path, method, payload);

    if (!ok) {
        errorBox.textContent = formatApiError(data);
        errorBox.classList.remove("d-none");
        return;
    }
    modalFor("expense-modal").hide();
    document.getElementById("expense-form").reset();
    await Promise.all([loadExpenses(), loadSummary(), loadBudget(), loadNotifications()]);
});

// ---------------------------------------------------------------- Notifications

async function loadNotifications() {
    const data = await apiGet("/api/notifications/");
    if (!data) return;

    const list = document.getElementById("notifications-list");
    const empty = document.getElementById("notifications-empty");
    const countBadge = document.getElementById("notifications-count");

    list.querySelectorAll(".notification-item").forEach((el) => el.remove());

    if (data.length === 0) {
        empty.classList.remove("d-none");
        countBadge.classList.add("d-none");
        return;
    }

    empty.classList.add("d-none");
    countBadge.textContent = data.length;
    countBadge.classList.remove("d-none");

    data.slice(0, 10).forEach((notification) => {
        const item = document.createElement("li");
        item.className = "notification-item px-2 py-1 border-bottom small";
        item.innerHTML = `<div class="fw-semibold">${notification.title}</div><div class="text-muted">${notification.message}</div>`;
        list.appendChild(item);
    });
}

// ---------------------------------------------------------------- Init

async function init() {
    // Categories must load first - expense filter/form dropdowns and the
    // expense table's category-name lookup both depend on it.
    await loadCategories();
    await Promise.all([loadSummary(), loadBudget(), loadNotifications(), loadExpenses(), loadIncome()]);
}

init();
