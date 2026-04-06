export function initAuth() {

    return Promise.all([
        fetch('../components/registerModal.html').then(res => res.text()),
        fetch('../components/loginModal.html').then(res => res.text())
    ]).then(([registerHtml, loginHtml]) => {

        document.getElementById('modal-container').innerHTML =
        registerHtml + loginHtml;

        bindModalButtons();
        initRoleSelector();

    });

}

function bindModalButtons() {
    document.getElementById("openSignup").addEventListener("click", () => {
        new bootstrap.Modal(document.getElementById("signupModal")).show();
    });

    document.getElementById("openLogin").addEventListener("click", () => {
        new bootstrap.Modal(document.getElementById("loginModal")).show();
    });
}

function initRoleSelector() {

    const roleBox = document.getElementById("roleBox");
    const roleMenu = document.getElementById("roleMenu");
    const roleText = document.getElementById("roleText");

    if (!roleBox) return; 

    roleBox.onclick = () => {
        roleMenu.classList.toggle("d-none");
    };

    document.querySelectorAll(".role-item").forEach(item => {
        item.onclick = () => {

        document.querySelectorAll(".role-item")
            .forEach(i => i.classList.remove("active"));

        item.classList.add("active");

        roleText.innerText = item.innerText;
        roleText.style.color = "#000";

        roleMenu.classList.add("d-none");
        };
    });

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".role-select")) {
        roleMenu.classList.add("d-none");
        }
    });
}