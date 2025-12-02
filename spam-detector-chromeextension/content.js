// Selectors for Gmail
const SELECTORS = {
  subject: "h2.hP",
  body: ".a3s.aiL", // Common selector for message body
  emailContainer: ".gs", // Surrounding container for an individual email
};

// Function to debounce the observer to avoid multiple calls
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Function to extract email data
function extractEmailData(emailElement) {
  const subjectElement = document.querySelector(SELECTORS.subject);

  // Note: emailElement passed here is the container .gs or similar
  // We need to find the body inside it.
  // If emailElement is null (which happened in previous logic), we might need to search document.

  const bodyElement = emailElement
    ? emailElement.querySelector(SELECTORS.body)
    : document.querySelector(SELECTORS.body);

  if (!subjectElement || !bodyElement) {
    return null;
  }

  const subject = subjectElement.innerText;
  const body_html = bodyElement.innerHTML;
  const body_plain = bodyElement.innerText;

  return {
    subject,
    body_html,
    body_plain,
    subjectElement, // Return this so we know where to inject the badge
  };
}

// Function to handle detecting the email view
const handleMutation = debounce(() => {
  const subjectElement = document.querySelector(SELECTORS.subject);

  // If we see a subject and haven't checked it yet
  if (subjectElement && !subjectElement.dataset.spamChecked) {
    const emailBodies = document.querySelectorAll(SELECTORS.body);
    if (emailBodies.length > 0) {
      // Grab the last body (assuming it's the relevant one in a thread)
      const lastBody = emailBodies[emailBodies.length - 1];
      const container = lastBody.closest(SELECTORS.emailContainer);

      const data = extractEmailData(container);

      if (data) {
        console.log("Email detected:", data.subject);
        subjectElement.dataset.spamChecked = "true";
        detectSpam(data);
      }
    }
  }
}, 1000);

async function detectSpam(data) {
  try {
    const payload = {
      subject: data.subject,
      body_plain: data.body_plain,
    };

    const response = await fetch(
      "http://localhost:8000/emails/email/detect_spam",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }
    );

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const result = await response.json();
    console.log("Spam detection result:", result);

    // result format: { "is_spam": true, "confidence": 0.5506385615577027 }
    handleSpamResult(result, data.subjectElement);
  } catch (error) {
    console.error("Error checking spam:", error);
  }
}

function handleSpamResult(result, subjectElement) {
  // Only show if it is spam
  if (result.is_spam) {
    const badge = document.createElement("span");
    badge.className = "spam-badge";

    // Format confidence as percentage
    const percentage = (result.confidence * 100).toFixed(1);
    badge.innerText = `SPAM (${percentage}%)`;

    subjectElement.appendChild(badge);
  } else {
    const badge = document.createElement("span");
    badge.className = "not-spam-badge";

    const percentage = (result.confidence * 100).toFixed(1);
    badge.innerText = `NOT SPAM(${percentage}%)`;
    subjectElement.appendChild(badge);
  }
}

// Observer configuration
const observerConfig = {
  childList: true,
  subtree: true,
};

// Create the observer
const observer = new MutationObserver(handleMutation);

// Start observing
observer.observe(document.body, observerConfig);

console.log("Gmail Spam Detector: Observer started");
