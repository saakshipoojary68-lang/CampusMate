const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatWindow = document.getElementById("chat-window");
const robotImage = "/static/images/campusmate-robot.png";

function addMessage(text, sender) {
  const row = document.createElement("div");
  row.className = `message ${sender}`;
  if (sender === "bot") {
    const avatar = document.createElement("img");
    avatar.className = "message-avatar";
    avatar.src = robotImage;
    avatar.alt = "CampusMate";
    row.appendChild(avatar);
  }
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(message) {
  addMessage(message, "user");
  input.value = "";
  input.disabled = true;
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message})
    });
    const data = await response.json();
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    addMessage(data.reply || "Sorry, I could not process that question.", "bot");
  } catch (error) {
    addMessage("I'm having trouble connecting right now. Please check that CampusMate is running and try again.", "bot");
  } finally {
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (message) sendMessage(message);
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    sendMessage(button.dataset.question);
  });
});
