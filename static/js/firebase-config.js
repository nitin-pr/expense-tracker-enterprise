import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyAApXpdS0vAuAiaE9oTXM-_lZjE18Bbr3M",
  authDomain: "expense-tracker-enterprise.firebaseapp.com",
  projectId: "expense-tracker-enterprise",
  storageBucket: "expense-tracker-enterprise.firebasestorage.app",
  messagingSenderId: "730850140189",
  appId: "1:730850140189:web:15ae1dc6957b5dcab5a6f4"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);