(function () {
  const tg = window.Telegram?.WebApp;
  const chatBox = document.getElementById("chatBox");
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const typing = document.getElementById("typing");

  if (tg) {
    tg.ready();
    tg.expand();
  }

  let history = JSON.parse(localStorage.getItem("suuz_chat_history") || "[]");

  function saveHistory() {
    localStorage.setItem("suuz_chat_history", JSON.stringify(history));
  }

  function addMessage(role, text) {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${role}`;
    bubble.textContent = text;
    chatBox.appendChild(bubble);
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
        addMessage("agent", data.reply);
        history.push({ role: "model", parts: [{ text: data.reply }] });
        // Keep history manageable
        if (history.length > 20) history = history.slice(-20);
        saveHistory();
      } else {
        addMessage("agent", "Kechirasiz, xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.");
      }
    } catch (err) {
      typing.style.display = "none";
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
