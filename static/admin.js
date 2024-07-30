const form = document.getElementById('info-form');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (response.status === 200) {
            showError("info", `${data.success}`);
        }
        else if (response.status === 302) {
            window.location.replace(data.redirect);
        }
        else {
            showError("error", `${data.error}`);
            form.querySelector('input').focus();
        }
    } 
    catch(error) {
        showError("error", `${data.error}`);
        form.querySelector('input').focus();
    }
});

function showError(type, message) {
    const errorMsg = document.getElementById("error-msg")
    if (type === "error") {
        document.getElementById('msg-icon').innerText = "error_outline";
        errorMsg.style.setProperty("background-color", "red");
    }
    else {
        document.getElementById('msg-icon').innerText = "info";
        errorMsg.style.setProperty("background-color", "rgb(174, 230, 129)");
    }
    document.getElementById('error-message').innerText = message;
    errorMsg.dataset.open = "true";
    setTimeout(() => {
        errorMsg.dataset.open = "false";
    }, 3000);
}

addEventListener("load", ()  => {
    console.log("hello");
    form.querySelector('input').focus();
});
