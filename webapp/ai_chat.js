(function () {
  const tg = window.Telegram?.WebApp;
  const chatBox = document.getElementById("chatBox");
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const typing = document.getElementById("typing");
  const scrollBtn = document.getElementById("scrollToBottom");
  const statusText = document.querySelector(".status-indicator span:last-child");
  const statusDot = document.querySelector(".status-dot");

  if (tg) {
    tg.ready();
    tg.expand();
  }

  let history = JSON.parse(localStorage.getItem("suuz_chat_history") || "[]");

  function saveHistory() {
    localStorage.setItem("suuz_chat_history", JSON.stringify(history));
  }

  function setStatus(isTyping) {
    if (isTyping) {
      statusText.textContent = "Yozmoqda...";
      statusDot.style.background = "#00a400";
    } else {
      statusText.textContent = "Online";
      statusDot.style.background = "#00a400";
    }
  }

  // Scroll to bottom logic
  chatBox.addEventListener("scroll", () => {
    const threshold = 300;
    const isScrolledUp = chatBox.scrollHeight - chatBox.clientHeight - chatBox.scrollTop > threshold;
    scrollBtn.style.display = isScrolledUp ? "flex" : "none";
  });

  scrollBtn.addEventListener("click", () => {
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
  });

  function formatMessage(text) {
    // Escape HTML to prevent XSS
    let escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");

    // Bold: **text** -> <b>text</b>
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");

    // Bullet points: * item or - item -> • item
    escaped = escaped.replace(/^[\s]*[\*\-][\s]+(.*)$/gm, "• $1");

    // Newlines: \n -> <br>
    escaped = escaped.replace(/\n/g, "<br>");

    return escaped;
  }

  async function typeWriter(element, text) {
    const speed = 15; // ms per character
    let currentText = "";
    const words = text.split("");
    
    for (const char of words) {
      currentText += char;
      element.innerHTML = formatMessage(currentText);
      chatBox.scrollTop = chatBox.scrollHeight;
      await new Promise(resolve => setTimeout(resolve, speed));
    }
  }

  async function addMessage(role, text, animate = false) {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${role}`;
    chatBox.appendChild(bubble);
    
    if (animate && role === "agent") {
      await typeWriter(bubble, text);
    } else {
      bubble.innerHTML = formatMessage(text);
    }
    
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // Initial render
  if (history.length === 0) {
    const welcomeText = "Assalomu alaykum! Men Sharda Universityning 'Suuz agent' virtual yordamchisiman. Sizga qanday yordam bera olaman?";
    addMessage("agent", welcomeText);
    // Don't save welcome to history unless you want it persistent
  } else {
    history.forEach(m => {
      addMessage(m.role === "user" ? "user" : "agent", m.parts[0].text);
    });
  }

  async function callAI(message) {
    typing.style.display = "flex";
    setStatus(true);
    chatBox.scrollTop = chatBox.scrollHeight;

    const userId = tg?.initDataUnsafe?.user?.id || "web_user";

    try {
      const response = await fetch("/api/ai_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message, 
          history: history.slice(-6), // Only send last 3 turns
          user_id: userId 
        })
      });

      const data = await response.json();
      typing.style.display = "none";

      if (data.reply) {
        await addMessage("agent", data.reply, true);
        setStatus(false);
        history.push({ role: "model", parts: [{ text: data.reply }] });
        // Keep history manageable
        if (history.length > 20) history = history.slice(-20);
        saveHistory();
      } else {
        setStatus(false);
        addMessage("agent", "Kechirasiz, xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.");
      }
    } catch (err) {
      typing.style.display = "none";
      setStatus(false);
      addMessage("agent", "Server bilan aloqa o'rnatib bo'lmadi.");
      console.error(err);
    }
  }

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    userInput.value = "";
    addMessage("user", text);
    
    // Format for Gemini API (matches our backend expectation)
    history.push({ role: "user", parts: [{ text }] });
    saveHistory();

    callAI(text);
  });
})();
