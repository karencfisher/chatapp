const conversation = document.getElementById("conversation");
function addMessage(msg, role) {
    const htmlContent = marked.parse(msg);
    const msgDiv = document.createElement("div");
    if (role === "AI" || role == 'assistant') {
        msgDiv.classList.add("AI-message");
    }
    else {
        msgDiv.classList.add("user-message");
    }
    msgDiv.innerHTML = htmlContent;
    conversation.appendChild(msgDiv);
    conversation.scrollTop = conversation.scrollHeight;
}

async function getResponse(prompt) {
    const query = { message: prompt };
    try {
        const result = await fetch(
            "/ask",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(query)
            }
        );
        const contents = await result.json();
        return contents.message;
    }
    catch(error) {
        displayError("Error", `Error sending message to model. Might be offline?`);
    }
}

async function clearSession() {
    try {
        await fetch('/clear_session');
    }
    catch(error) {
        displayError("error", "Could not clear session. Might be offline?")
    }
}

const promptText = document.getElementById("prompt-text");
const sendButton = document.getElementById("send-button");
const cancelButton = document.getElementById("cancel-button");

async function sendPrompt(new_chat) {
    document.body.style.cursor = 'wait';
    const prompt = promptText.value.trim();

    if (new_chat) {
        await clearSession();
        conversation.innerHTML = "";
    }

    addMessage(prompt, "user");
    let result = null;
    try {
        result = await getResponse(prompt);
        addMessage(result, "AI");
    }
    catch(error) {
        displayError("error", `Error: ${error}`)
    }
    document.body.style.cursor = 'default';
}

function toggleTabIndexes() {
    let newIndex = 0;
    if (promptText.getAttribute("tabindex") === "0") {
        newIndex = -1;
    }

    promptText.setAttribute("tabindex", `${newIndex}`);
    sendButton.setAttribute("tabindex", `${newIndex}`);
    cancelButton.setAttribute("tabindex", `${newIndex}`);
}

const prompt = document.getElementById("prompt");
const mask = document.getElementById("mask");
let promptState = false
function togglePrompt() {
    promptState = !promptState;
    prompt.dataset.open = `${promptState}`;
    mask.dataset.open = `${promptState}`;
    promptText.value = "";
    if (promptState) {
        promptText.focus();
        promptText.inputMode = "text";
    }
    else {
        promptText.inputMode = "none";
    }
    toggleTabIndexes();
}

addEventListener("load", async () => {
    try {
        const result = await fetch("/conversation");
        const conversation = await result.json();
        for (message of conversation) {
            addMessage(message.content, message.role)
        }
    }
    catch(error) {
        displayError("Error", `Error fetching conversation. Might be offline?`);
    }
});

sendButton.addEventListener("click", () => {
    if (promptText.value === "") {
        displayError("error", "Prompt is empty!")
        return;
    }

    const newButton = document.getElementById('new-button');
    sendPrompt(newButton.checked);
    newButton.checked = false;
    togglePrompt();
});

cancelButton.addEventListener("click", () => {
    togglePrompt();
});

const promptButton = document.getElementById("prompt-button");
promptButton.addEventListener("click", () => {
    togglePrompt();
});

const downloadBoxButton = document.getElementById("download-box-button");
const downloadBox = document.getElementById("download-box");
let boxOpen = false;
downloadBoxButton.addEventListener("click", () => {
    boxOpen = !boxOpen;
    downloadBox.dataset.open = `${boxOpen}`;
    mask.dataset.open = `${boxOpen}`;
});

const logoutButton = document.getElementById("logout-button");
logoutButton.addEventListener("click", async () => {
    response = await fetch("/logout");
    if (response.status === 200) {
        window.location.href = response.url;
    }
});

mask.addEventListener("click", () => {
    if (downloadBox.dataset.open === "true") {
        downloadBox.dataset.open = "false";
        mask.dataset.open = "false";
        boxOpen = false;
    }
    else if (prompt.dataset.open === "true") {
        togglePrompt();
    }
});

const downloadButton = document.getElementById("download-button");
downloadButton.addEventListener("click", () => {
    if (document.getElementById("chat-title").value === "" || conversation.childElementCount === 0) {
        displayError("error", "Chat title or conversation is empty!");
        return;
    }
    const chatLog = document.createElement("div");
    const chatTitleField = document.createElement("h2");
    chatTitleField.innerText = document.getElementById("chat-title").value;
    chatLog.appendChild(chatTitleField);

    for (const child of conversation.children) {
        let role = "Human";
        if (child.className === "AI-message") {
            role ="AI";
        }
        const msg = document.createElement("p");
        msg.style.setProperty("word-wrap", "break-word");
        msg.innerHTML = `<b>${role}:</b> ${child.innerHTML}\n\n`;
        chatLog.appendChild(msg);
    }

    const blob = new Blob([chatLog.innerHTML], { type: "text/html"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${chatTitleField.innerText.replace(" ", "_")}.html`
    a.click();
    URL.revokeObjectURL(a.href);
    URL.revokeObjectURL(chatLog);
});

function displayError(type, msg) {
    const errorMsg = document.getElementById("error-msg");
    const errortxt = document.getElementById("error-txt");
    const msgIcon = document.getElementById("msg-icon");
    if (type === "info") {
        msgIcon.innerText = "info";
    }
    else {
        msgIcon.innerText = "error_outline";
    }

    errortxt.innerText = msg;
    errorMsg.dataset.open = "true";
    mask.dataset.open = "true";

    setTimeout(() => {
        errorMsg.dataset.open = "false";
        mask.dataset.open = "false";
    }, 2000);
}

