(function () {
  const form = document.getElementById("exam-form");
  const timerBox = document.getElementById("timer");
  const timerText = document.getElementById("timer-text");
  const bar = document.getElementById("progress-bar");
  const answeredText = document.getElementById("answered-text");
  const questions = Array.from(document.querySelectorAll(".question"));
  const palette = Array.from(document.querySelectorAll("#palette button"));
  const prev = document.getElementById("prev");
  const next = document.getElementById("next");
  const submitBtn = document.getElementById("submit-btn");
  const total = questions.length;
  let current = 0;
  let submitting = false;

  // ---- question navigation -------------------------------------------------
  function show(index) {
    current = Math.max(0, Math.min(total - 1, index));
    questions.forEach((q, i) => { q.hidden = i !== current; });
    prev.disabled = current === 0;
    next.disabled = current === total - 1;
    refreshPalette();
  }

  function isAnswered(i) {
    return !!questions[i].querySelector("input:checked");
  }

  function refreshPalette() {
    let answered = 0;
    palette.forEach((btn, i) => {
      const done = isAnswered(i);
      if (done) answered += 1;
      btn.classList.toggle("done", done);
      btn.classList.toggle("current", i === current);
    });
    answeredText.textContent = answered + " of " + total + " answered";
    bar.style.width = (answered / total * 100) + "%";
    return answered;
  }

  prev.addEventListener("click", () => show(current - 1));
  next.addEventListener("click", () => show(current + 1));
  palette.forEach((btn) => btn.addEventListener("click", () => show(Number(btn.dataset.go))));
  form.addEventListener("change", refreshPalette);

  // ---- submitting ------------------------------------------------------------
  function submitNow() {
    if (submitting) return;
    submitting = true;
    form.submit();
  }

  submitBtn.addEventListener("click", () => {
    const unanswered = total - refreshPalette();
    const message = unanswered
      ? "You have " + unanswered + " unanswered question" + (unanswered > 1 ? "s" : "") + ". Submit anyway?"
      : "Submit your exam now? You cannot change answers afterwards.";
    if (window.confirm(message)) submitNow();
  });

  window.addEventListener("beforeunload", (event) => {
    if (!submitting) { event.preventDefault(); event.returnValue = ""; }
  });

  // ---- countdown (based on the server's remaining time) ---------------------
  const endsAt = Date.now() + Number(timerBox.dataset.seconds) * 1000;

  function tick() {
    const left = Math.max(0, Math.round((endsAt - Date.now()) / 1000));
    const m = String(Math.floor(left / 60)).padStart(2, "0");
    const s = String(left % 60).padStart(2, "0");
    timerText.textContent = m + ":" + s;
    timerBox.classList.toggle("low", left <= 60);
    if (left === 0) {
      clearInterval(interval);
      submitNow();
    }
  }
  const interval = setInterval(tick, 1000);
  tick();
  show(0);
})();
