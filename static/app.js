const $ = (id) => document.getElementById(id);
const state = { original: "", task: "", lang: "java" };

const SAMPLES = {
  java: {
    task: "Print the multiplication table of 7 from 1 to 10",
    code: `public class Table {
    public static void main(String[] args) {
        int n = 7
        for (int i = 1; i <= 10; i+) {
            System.out.println(n + " x " + i + " = " + n * i)
        }
    }
}`
  },
  xml: {
    task: "A login screen with an email field, a password field and a Login button",
    code: `<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertikal"
    android:padding="16dp">

    <EditText
        android:id="@+id/email"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Email"
        android:inputType="textEmailAddres" />

    <EditText
        android:id="@+id/password"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Password" />

    <Button
        android:id="@+id/loginBtn"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Login"
</LinearLayout>`
  }
};

document.querySelectorAll(".lang-btn").forEach(b => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".lang-btn").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    state.lang = b.dataset.lang;
  });
});

document.querySelectorAll(".sample-btn").forEach(b => {
  b.addEventListener("click", () => {
    const s = SAMPLES[b.dataset.sample];
    $("task").value = s.task;
    $("code").value = s.code;
    document.querySelectorAll(".lang-btn").forEach(x =>
      x.classList.toggle("active", x.dataset.lang === b.dataset.sample));
    state.lang = b.dataset.sample;
  });
});

function showLoading(on, text) {
  $("loadingText").textContent = text || "Muse Spark Open is reading your code...";
  $("loading").hidden = !on;
}

async function post(url, payload) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || `Request failed (${r.status})`);
  return data;
}

$("debugBtn").addEventListener("click", async () => {
  const code = $("code").value.trim();
  const task = $("task").value.trim();
  $("debugError").hidden = true;
  if (!code) { $("debugError").textContent = "Paste your practical code first."; $("debugError").hidden = false; return; }
  $("debugBtn").disabled = true;
  showLoading(true);
  try {
    const data = await post("/api/debug", { code, task });
    state.original = code;
    state.task = task;
    renderResults(data);
  } catch (e) {
    $("debugError").textContent = e.message;
    $("debugError").hidden = false;
  } finally {
    $("debugBtn").disabled = false;
    showLoading(false);
  }
});

function renderResults(data) {
  $("results").hidden = false;
  $("verdictBox").hidden = true;
  const list = $("bugList");
  list.innerHTML = "";
  data.bugs.forEach((b, i) => {
    const li = document.createElement("li");
    const num = document.createElement("span");
    num.className = "bnum";
    num.textContent = i + 1;
    const txt = document.createElement("span");
    txt.textContent = b;
    li.append(num, txt);
    list.appendChild(li);
  });
  $("bugCount").textContent = `${data.bugs.length} bug${data.bugs.length === 1 ? "" : "s"} found`;
  $("takeawayText").textContent = data.takeaway;
  $("fixedCode").textContent = data.fixed_code;
  $("results").scrollIntoView({ behavior: "smooth", block: "start" });
}

$("copyFix").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("fixedCode").textContent);
  $("copyFix").lastChild.textContent = " Copied!";
  setTimeout(() => { $("copyFix").lastChild.textContent = " Copy"; }, 1400);
});

$("verifyBtn").addEventListener("click", async () => {
  $("verifyError").hidden = true;
  $("verifyBtn").disabled = true;
  showLoading(true, "AI re-check in progress...");
  try {
    const data = await post("/api/verify", {
      original: state.original,
      fixed: $("fixedCode").textContent,
      task: state.task
    });
    const box = $("verdictBox");
    const badge = $("verdictBadge");
    badge.textContent = "AI review: " + data.verdict;
    badge.className = "verdict-badge " + (data.verdict === "PASS" ? "pass" : "fail");
    const why = $("verdictWhy");
    why.innerHTML = "";
    data.why.forEach(w => {
      const li = document.createElement("li");
      li.textContent = w;
      why.appendChild(li);
    });
    box.hidden = false;
    box.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (e) {
    $("verifyError").textContent = e.message;
    $("verifyError").hidden = false;
  } finally {
    $("verifyBtn").disabled = false;
    showLoading(false);
  }
});
