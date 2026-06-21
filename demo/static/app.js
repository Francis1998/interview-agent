const btn = document.getElementById("ask-btn");
const answerEl = document.getElementById("answer");
const tracesEl = document.getElementById("traces");
const eventsEl = document.getElementById("events");

btn.addEventListener("click", async () => {
  const question = document.getElementById("question").value.trim();
  if (!question) return alert("Enter a question");

  btn.disabled = true;
  btn.textContent = "Running agent…";
  answerEl.textContent = "Planning → Retrieving → Reasoning → Answering…";
  tracesEl.innerHTML = "";
  eventsEl.innerHTML = "";

  const topic = document.getElementById("topic").value;
  const provider = document.getElementById("provider").value;
  const difficulty = document.getElementById("difficulty").value;

  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        topic_hint: topic || null,
        provider: provider || null,
        difficulty,
      }),
    });
    const data = await res.json();
    answerEl.textContent = data.answer || data.error || "No response";
    (data.rationale_traces || []).forEach((t) => {
      const div = document.createElement("div");
      div.className = "trace";
      div.innerHTML = `<strong>${t.step}</strong> → ${t.chosen}<br/><span>${t.reason}</span>`;
      tracesEl.appendChild(div);
    });
    (data.events || []).forEach((e) => {
      const div = document.createElement("div");
      div.className = "event";
      div.innerHTML = `<strong>${e.event_type}</strong> <small>${e.timestamp}</small>`;
      eventsEl.appendChild(div);
    });
  } catch (err) {
    answerEl.textContent = "Error: " + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Run Agent";
  }
});
