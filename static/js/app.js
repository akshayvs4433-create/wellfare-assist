/**
 * WelfareAI - Client JavaScript
 * Handles Web Speech API voice input, demo household modal, and accessibility enhancements.
 */

document.addEventListener("DOMContentLoaded", function () {
  initVoiceInput();
  initDemoModal();
  initRadioCards();
});

/**
 * Web Speech API Voice Input
 * Provides microphone-driven transcription for number & text fields.
 * Supports English (en-IN) and Malayalam (ml-IN).
 */
function initVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const voiceButtons = document.querySelectorAll(".btn-voice");

  if (!SpeechRecognition) {
    // If Web Speech API not supported in the user's browser, hide or disable mic buttons gently
    voiceButtons.forEach(btn => {
      btn.title = "Voice recognition is supported in Chrome, Edge, and Safari browsers.";
      btn.style.opacity = "0.7";
      btn.addEventListener("click", () => {
        alert("Voice input requires a browser that supports the Web Speech API (e.g. Chrome, Edge, Safari). You can still type directly into the field.");
      });
    });
    return;
  }

  // Determine language code based on html lang attribute
  const docLang = document.documentElement.lang || "en";
  const speechLang = docLang === "ml" ? "ml-IN" : "en-IN";

  voiceButtons.forEach(btn => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const targetInputId = btn.getAttribute("data-target");
      const targetInput = document.getElementById(targetInputId);
      if (!targetInput) return;

      const recognition = new SpeechRecognition();
      recognition.lang = speechLang;
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      const originalBtnText = btn.innerHTML;
      btn.classList.add("listening");
      btn.innerHTML = docLang === "ml" ? "🎙️ കേൾക്കുന്നു..." : "🎙️ Listening...";

      recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        // Clean up transcript
        let cleanText = transcript.trim();

        // If field is number/income/age, parse digits
        if (targetInput.type === "number" || targetInputId.includes("income") || targetInputId.includes("age") || targetInputId.includes("family")) {
          // Remove commas and spaces
          const numMatch = cleanText.replace(/,/g, "").match(/\d+/);
          if (numMatch) {
            targetInput.value = numMatch[0];
          } else {
            // Check for words like "forty two", "two lakhs", etc.
            targetInput.value = cleanText;
          }
        } else {
          targetInput.value = cleanText;
        }

        // Trigger change event
        targetInput.dispatchEvent(new Event("change", { bubbles: true }));
      };

      recognition.onerror = function (event) {
        console.warn("Speech recognition error:", event.error);
        if (event.error === "not-allowed") {
          alert("Microphone permission was not granted. Please allow microphone access in your browser settings to use voice input.");
        }
      };

      recognition.onend = function () {
        btn.classList.remove("listening");
        btn.innerHTML = originalBtnText;
      };

      try {
        recognition.start();
      } catch (err) {
        console.warn("Speech recognition start failed:", err);
        btn.classList.remove("listening");
        btn.innerHTML = originalBtnText;
      }
    });
  });
}

/**
 * Demo Household Modal
 */
function initDemoModal() {
  const modal = document.getElementById("demoModal");
  const openBtns = document.querySelectorAll(".btn-open-demo");
  const closeBtns = document.querySelectorAll(".btn-close-modal, .demo-modal-backdrop");

  if (!modal) return;

  openBtns.forEach(btn => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      modal.classList.add("show");
      document.body.style.overflow = "hidden";
    });
  });

  closeBtns.forEach(btn => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      modal.classList.remove("show");
      document.body.style.overflow = "";
    });
  });

  // Close on Escape
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.classList.contains("show")) {
      modal.classList.remove("show");
      document.body.style.overflow = "";
    }
  });
}

/**
 * Radio Cards Selection Styling
 */
function initRadioCards() {
  const radioCards = document.querySelectorAll(".radio-card");
  radioCards.forEach(card => {
    const radio = card.querySelector("input[type='radio']");
    if (!radio) return;

    if (radio.checked) {
      card.classList.add("selected");
    }

    card.addEventListener("click", function (e) {
      // If clicking the card itself (not directly on input)
      if (e.target !== radio) {
        radio.checked = true;
      }

      // Deselect siblings
      const groupName = radio.name;
      document.querySelectorAll(`input[name="${groupName}"]`).forEach(sibling => {
        const parent = sibling.closest(".radio-card");
        if (parent) parent.classList.remove("selected");
      });

      card.classList.add("selected");
    });
  });
}

