import { auth } from "./firebase-config.js";
import { sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getFriendlyErrorMessage } from "./auth-errors.js";

const form = document.getElementById("forgot-password-form");
const errorAlert = document.getElementById("error-alert");
const successAlert = document.getElementById("success-alert");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorAlert.classList.add("d-none");
    successAlert.classList.add("d-none");

    const email = document.getElementById("email").value;

    try {
        await sendPasswordResetEmail(auth, email);
        form.classList.add("d-none");
        // Deliberately generic wording: doesn't confirm/deny whether the email
        // has an account, same "avoid user enumeration" reasoning as login errors.
        successAlert.textContent = "If an account exists for that email, a password reset link has been sent.";
        successAlert.classList.remove("d-none");
    } catch (error) {
        errorAlert.textContent = getFriendlyErrorMessage(error);
        errorAlert.classList.remove("d-none");
    }
});
