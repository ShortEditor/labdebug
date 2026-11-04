"""LabDebug - a lab-debugging assistant for college practicals.

Paste a broken Java or Android XML practical; LabDebug explains each bug,
shows the fix, and strictly re-checks your corrected program.

Muse Spark Open (Meta's open-weight coding model), served through Baseten's
OpenAI-compatible Model API, is the core reasoning engine: every bug
analysis and fix verification is a Muse Spark Open call.
"""

import os
import re
import requests
from flask import Flask, jsonify, render_template, request

BASETEN_URL = "https://inference.baseten.co/v1/chat/completions"
MODEL = "meta-models/muse-spark-open"
API_KEY = os.environ.get("BASETEN_API_KEY", "")

SYSTEM_PROMPT = (
    "You are LabDebug, a patient lab instructor for Indian polytechnic "
    "diploma practicals (Java, Android XML). Given a broken lab program and "
    "optionally what it should do, reply in exactly this format:\n"
    "BUGS:\n"
    "- one line per bug: what is wrong and why it breaks\n"
    "FIXED CODE:\n"
    "```\n"
    "<the full corrected program, nothing else inside the fences>\n"
    "```\n"
    "TAKEAWAY:\n"
    "one sentence on what to learn from this. The takeaway must be\n"
    "narrowly true about these specific bugs; never state broad language\n"
    "rules like \"every statement must...\".\n"
    "Be accurate and brief. Do not invent requirements."
)

VERIFY_PROMPT = (
    "You are LabDebug, a strict lab examiner for diploma practicals. "
    "You are given the original task, the broken program and the student's "
    "corrected program. Reply in exactly this format:\n"
    "VERDICT: PASS or FAIL\n"
    "WHY:\n"
    "- one or two lines on what is now correct or what still breaks\n"
    "This is a static review: never claim you compiled or executed the code;\n"
    "say \"would compile/run\", not \"compiles/runs\".\n"
    "Be strict: only PASS if the corrected program would actually run and "
    "meet the task."
)

app = Flask(__name__)


def ask_muse(system_prompt, user_prompt, max_tokens=1500):
    """One Muse Spark Open call via Baseten. Returns (text, usage_dict)."""
    headers = {"Authorization": f"Bearer {API_KEY}",
               "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
    }
    r = requests.post(BASETEN_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    msg = data["choices"][0]["message"]
    text = msg.get("content") or msg.get("reasoning_content") or ""
    return text, data.get("usage", {})


def parse_debug(text):
    # Tolerate markdown decoration, same-line content and missing fences.
    clean = text.replace("**", "")
    m = re.search(r"FIXED CODE:", clean)
    if not m:
        return {"bugs": [], "fixed_code": "", "takeaway": clean.strip()}
    head, tail = clean[:m.start()], clean[m.end():]

    bugs = []
    bm = re.search(r"BUGS:\s*:?\s*\n?(.*)", head, re.S)
    if bm:
        for ln in bm.group(1).strip().splitlines():
            ln = ln.lstrip("- ").strip().rstrip(";")
            if ln:
                bugs.append(ln)

    fm = re.search(r"```(?:\w+)?\n(.*?)```", tail, re.S)
    if fm:
        fixed = fm.group(1).strip("\n")
        rest = tail[fm.end():]
    else:
        fixed, rest = "", tail

    takeaway = ""
    tm = re.search(r"TAKEAWAY:\s*:?\s*\n?(.*)", rest, re.S)
    if tm:
        takeaway = tm.group(1).strip()
    elif not fm:
        takeaway = rest.strip()
    return {"bugs": bugs, "fixed_code": fixed, "takeaway": takeaway}


def parse_verify(text):
    verdicts = list(re.finditer(r"VERDICT:\s*(PASS|FAIL)", text, re.I))
    if not verdicts:
        return {"verdict": "FAIL", "why": ["Could not parse the examiner reply."]}
    last = verdicts[-1]
    verdict = last.group(1).upper()
    tail = text[last.end():]
    m = re.search(r"WHY:\s*\n(.*)", tail, re.S)
    why = []
    if m:
        for ln in m.group(1).strip().splitlines():
            ln = ln.lstrip("- ").strip()
            if ln and not ln.startswith("```"):
                why.append(ln)
            if len(why) == 3:
                break
    return {"verdict": verdict, "why": why or ["No reason given."]}


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/debug")
def debug():
    body = request.get_json(force=True)
    code = (body.get("code") or "").strip()
    task = (body.get("task") or "").strip()
    if not code:
        return jsonify({"error": "Paste your practical code first."}), 400
    user = f"TASK: {task or 'not specified'}\n\nBROKEN CODE:\n{code}"
    try:
        text, usage = ask_muse(SYSTEM_PROMPT, user)
    except requests.HTTPError as e:
        return jsonify({"error": f"Model API error: {e.response.status_code}"}), 502
    out = parse_debug(text)
    out["usage"] = usage
    return jsonify(out)


@app.post("/api/verify")
def verify():
    body = request.get_json(force=True)
    original = (body.get("original") or "").strip()
    fixed = (body.get("fixed") or "").strip()
    task = (body.get("task") or "").strip()
    if not original or not fixed:
        return jsonify({"error": "Need both the original and your fixed code."}), 400
    user = (f"TASK: {task or 'not specified'}\n\nBROKEN CODE:\n{original}"
            f"\n\nSTUDENT'S CORRECTED CODE:\n{fixed}")
    try:
        text, usage = ask_muse(VERIFY_PROMPT, user, max_tokens=1400)
    except requests.HTTPError as e:
        return jsonify({"error": f"Model API error: {e.response.status_code}"}), 502
    out = parse_verify(text)
    out["usage"] = usage
    return jsonify(out)


if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("Set BASETEN_API_KEY first.")
    app.run(host="127.0.0.1", port=5000, debug=False)
