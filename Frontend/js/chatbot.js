
document.addEventListener("DOMContentLoaded", () => {
  // FastAPI backend endpoint deployed on Render
  const API_URL = "https://my-portfolio-ai-iwea.onrender.com/chat";

  // Connect to your existing HTML elements
  const toggle = document.getElementById("chatbotToggle");
  const windowEl = document.getElementById("chatbotWindow");
  const close = document.getElementById("chatbotClose");
  const messages = document.getElementById("chatbotMessages");
  const input = document.getElementById("chatbotInput");
  const send = document.getElementById("chatbotSend");
  const typing = document.getElementById("chatbotTyping");
  const suggestions = document.getElementById("chatSuggestions");

  // Check required HTML elements
  if (
    !toggle ||
    !windowEl ||
    !close ||
    !messages ||
    !input ||
    !send ||
    !typing
  ) {
    console.error(
      "Chatbot initialization failed: Required HTML elements are missing."
    );
    return;
  }

  // Open and close the chatbot
  function setChatbotOpen(open) {
    windowEl.classList.toggle("active", open);
    windowEl.setAttribute("aria-hidden", String(!open));
    toggle.setAttribute("aria-expanded", String(open));

    if (open) {
      input.focus();
    }
  }

  toggle.addEventListener("click", () => {
    setChatbotOpen(!windowEl.classList.contains("active"));
  });

  close.addEventListener("click", () => {
    setChatbotOpen(false);
  });

  // Add a message to the chatbot window
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

    // Safely display message text
    content.textContent = text;

    message.appendChild(content);
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;

    return message;
  }

  // Send a question to FastAPI
  async function sendQuestion(question) {
    question = question.trim();

    if (!question || send.disabled) {
      return;
    }

    // Display the user's question
    addMessage(question, "user");

    // Hide suggested questions after the first question
    if (suggestions) {
      suggestions.style.display = "none";
    }

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

      // Handle JSON and unexpected server responses
      const contentType = response.headers.get("content-type") || "";

      if (!contentType.includes("application/json")) {
        const responseText = await response.text();

        throw new Error(
          `Server returned status ${response.status}. ` +
          `Unexpected response: ${responseText.slice(0, 200)}`
        );
      }

      const data = await response.json();

      // Handle HTTP errors
      if (!response.ok) {
        throw new Error(
          data.detail || `Request failed with status ${response.status}`
        );
      }

      // Expected FastAPI response:
      // { "question": "...", "answer": "..." }
      const answer = data.answer;

      if (typeof answer !== "string" || !answer.trim()) {
        throw new Error(
          "The backend response does not contain a valid answer."
        );
      }

      // Display the bot's response
      addMessage(answer, "bot");

    } catch (error) {
      console.error("Chatbot error:", error);

      let errorMessage =
        "Sorry, I couldn't get a response. Please try again.";

      if (error instanceof TypeError) {
        errorMessage =
          "Unable to connect to the chatbot server. Please check your connection and try again.";
      } else if (error.message.includes("405")) {
        errorMessage =
          "The server rejected the request method. Please verify that the API URL ends with /chat.";
      } else if (error.message.includes("500")) {
        errorMessage =
          "The chatbot server encountered an error. Please check the Render logs and OpenRouter API configuration.";
      } else if (error.message.toLowerCase().includes("failed to fetch")) {
        errorMessage =
          "Could not reach the chatbot server. Check the backend status and CORS configuration.";
      }

      addMessage(errorMessage, "bot");

    } finally {
      // Restore chatbot controls
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

  // Press Enter to send; allow Shift+Enter for a newline
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendQuestion(input.value);
    }
  });

  // Connect suggested-question buttons
  document.querySelectorAll(".suggestion-btn").forEach((button) => {
    button.addEventListener("click", () => {
      sendQuestion(button.textContent);
    });
  });
});
