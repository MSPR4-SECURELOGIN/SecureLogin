// Connexion utilisateur
const faasUser = "admin";
const faasPassword = "bn7swFFkjYBA"; // Mets ici le mot de passe trouvé via kubectl
const authHeader = "Basic " + btoa(faasUser + ":" + faasPassword);

document.getElementById("loginForm")?.addEventListener("submit", async function (e) {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const code2fa = document.getElementById("code2fa").value;

  try {
    const response = await fetch("http://localhost:8080/function/authenticate-user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": authHeader
      },
      body: JSON.stringify({ username, password, code2fa })
    });

    const result = await response.json();

    if (result.authenticated) {
      window.location.href = "home.html";
    } else if (result.expired) {
      document.getElementById("renewSection").classList.remove("d-none");
      localStorage.setItem("usernameToRenew", username);
    } else {
      alert(result.error || "Échec de la connexion.");
    }
  } catch (err) {
    console.error(err);
    alert("Erreur réseau lors de la connexion.");
  }
});

// Renouvellement de compte expiré
async function renewAccount() {
  const username = localStorage.getItem("usernameToRenew");
  if (!username) return;

  try {
    const response = await fetch("http://localhost:8080/function/renew-user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": authHeader
      },
      body: JSON.stringify({ username })
    });

    const result = await response.json();

    if (result.success) {
      document.getElementById("newPassword").textContent = result.new_password;
      document.getElementById("qrCode").src = "data:image/png;base64," + result.totp_qr_base64;
      document.getElementById("renewResult").style.display = "block";
    } else {
      alert("Erreur : " + result.error);
    }
  } catch (err) {
    console.error(err);
    alert("Erreur réseau lors du renouvellement.");
  }
}

// Création d’un nouveau compte
document.getElementById("createForm")?.addEventListener("submit", async function (e) {
  e.preventDefault();

  const newUsername = document.getElementById("newUsername").value;

  try {
    const response = await fetch("http://localhost:8080/function/create-user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": authHeader
      },
      body: JSON.stringify({ username: newUsername })
    });

    const result = await response.json();

    if (result.success) {
      document.getElementById("generatedPassword").textContent = result.password;
      document.getElementById("generatedQr").src = "data:image/png;base64," + result.totp_qr_base64;
      document.getElementById("createResult").style.display = "block";
    } else {
      alert("Erreur : " + result.error);
    }
  } catch (err) {
    console.error(err);
    alert("Erreur réseau lors de la création du compte.");
  }
});
