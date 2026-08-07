import { auth } from "./firebase-config.js";
import { createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getFriendlyErrorMessage } from "./auth-errors.js";

const form = document.getElementById("signup-form");
const errorAlert = document.getElementById("error-alert");
const tokenDisplay = document.getElementById("token-display");
const tokenText = document.getElementById("token-text");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorAlert.classList.add("d-none");

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const idToken = await userCredential.user.getIdToken();
        sessionStorage.setItem("idToken", idToken);

        form.classList.add("d-none");
        tokenDisplay.classList.remove("d-none");
        tokenText.value = idToken;
    } catch (error) {
        errorAlert.textContent = getFriendlyErrorMessage(error);
        errorAlert.classList.remove("d-none");
    }
});
