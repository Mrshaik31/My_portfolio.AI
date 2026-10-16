
document.addEventListener("DOMContentLoaded", () => {
  // FastAPI backend endpoint
  const API_URL = "http://127.0.0.1:8000/chat";

  // Connect to your existing HTML elements
  const toggle = document.getElementById("chatbotToggle");
  const windowEl = document.getElementById("chatbotWindow");
  const close = document.getElementById("chatbotClose");
  const messages = document.getElementById("chatbotMessages");
  const input = document.getElementById("chatbotInput");
  const send = document.getElementById("chatbotSend");
  const typing = document.getElementById("chatbotTyping");
  const suggestions = document.getElementById("chatSuggestions");

  // Open and close the chatbot
  function setChatbotOpen(open) {
    windowEl.classList.toggle("active", open);
    windowEl.setAttribute("aria-hidden", String(!open));
    toggle.setAttribute("aria-expanded", String(open));

    if (open) input.focus();
  }

  toggle.addEventListener("click", () => {
    setChatbotOpen(!windowEl.classList.contains("active"));
  });

  close.addEventListener("click", () => {
    setChatbotOpen(false);
  });

  // Create a message matching your existing HTML/CSS
  function addMessage(text, sender) {
    const message = document.createElement("div");
    message.classList.add("chat-message", `${sender}-message`);

    if (sender === "bot") {
      const avatar = document.createElement("div");
      avatar.className = "message-avatar";

      const icon = document.createElement("i");
      icon.className = "bi bi-stars";
      avatar.appendChild(icon);

      message.appendChild(avatar);
    }

    const content = document.createElement("div");
    content.className = "message-content";

    // Use textContent to safely display the response
    content.textContent = text;
    message.appendChild(content);

    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;

    return message;
  }

  // Send a question to FastAPI
  async function sendQuestion(question) {
    question = question.trim();
    if (!question || send.disabled) return;

    // Display the user's question
    addMessage(question, "user");

    // Hide suggested questions after the first question
    if (suggestions) suggestions.style.display = "none";

    input.value = "";
    input.disabled = true;
    send.disabled = true;
    typing.style.display = "flex";

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          question: question
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || `Request failed: ${response.status}`
        );
      }

      // Expected response from FastAPI: {"answer": "..."}
      const answer = data.answer;

      if (typeof answer !== "string" || !answer.trim()) {
        throw new Error(
          "The backend response does not contain a valid 'answer' field."
        );
      }

      addMessage(answer, "bot");

    } catch (error) {
      console.error("Chatbot error:", error);

      addMessage(
        "Sorry, I couldn't get a response. Please check that the backend is running and the OpenRouter API is configured correctly, then try again.",
        "bot"
      );

    } finally {
      typing.style.display = "none";
      input.disabled = false;
      send.disabled = false;
      input.focus();
      messages.scrollTop = messages.scrollHeight;
    }
  }

  // Send button
  send.addEventListener("click", () => {
    sendQuestion(input.value);
  });

  // Press Enter to send
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendQuestion(input.value);
    }
  });

  // Connect your four suggested-question buttons
  document.querySelectorAll(".suggestion-btn").forEach((button) => {
    button.addEventListener("click", () => {
      sendQuestion(button.textContent);
    });
  });
});
