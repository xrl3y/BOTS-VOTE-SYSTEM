# 📘 README — Playwright Controlled Load Tester

## 🧩 Overview
This repository contains a **browser-based testing tool** built with **Playwright**.  
It is designed for **controlled, authorized environments only**, such as:

- 🧪 Staging servers  
- 🛠️ Internal QA environments  
- 🔐 Security audits  
- 🚀 Load and stress testing labs  

The script demonstrates how to automate **form submissions using a real browser**, capable of executing:

- ⚙️ JavaScript challenges  
- 🍪 Session/cookie handling  
- 📨 FormData POST requests  
- 🖥️ Dynamic rendering  

⚠️ **IMPORTANT:**  
This tool must only be used where you have **explicit authorization**.  
Do **NOT** use it on third‑party websites or production systems.

---

# ⚙️ Main Features

### ✔️ 1. Real Browser Automation
Using Playwright (Firefox/Chromium/WebKit):

- Executes JS challenges  
- Manages cookies/auth sessions  
- Behaves like a real user browser  

---

### ✔️ 2. Form Submission via `fetch()` Inside Browser
Submits forms using `FormData` and a real in-page `fetch()` call:

```js
const resp = await fetch(url, { method: "POST", body: fd });
```

---

### ✔️ 3. Automatic `trace_id` Generation
Each request receives a unique trace ID:

```python
trace = f"cli-{uuid.uuid4()}"
```

Useful for debugging and log analysis.

---

### ✔️ 4. Sequential or Parallel Execution
- **Sequential mode:** one request at a time  
- **Parallel mode:** Python multiprocessing launches several Playwright browsers simultaneously  

---

### ✔️ 5. Optional Nonce Extraction
If the environment generates hidden form nonces, the script automatically detects:

```python
el = page.query_selector('input[name="_nonce"]')
```

---

### ✔️ 6. Fully Customizable Parameters
You can modify:

- Number of attempts  
- Number of workers  
- Delays  
- Timeouts  
- Headless mode  
- Payload  
- Success markers  
- Selectors to wait for  

---

# 🚀 How to Use

## 1. Install Dependencies

### Install Playwright + Browsers:
```bash
pip install playwright
playwright install
```

### Extra Python modules:
```bash
pip install argparse
```

---

## 2. Run Script in **Sequential Mode**

```bash
python3 tester.py --reps 5
```

---

## 3. Headless Mode

```bash
python3 tester.py --reps 5 --headless
```

---

## 4. Run in **Parallel Mode**

```bash
python3 tester.py --reps 20 --parallel --workers 4
```

---

## 5. Add Delays

```bash
python3 tester.py --reps 10 --delay 1.5
```

Parallel mode delay:

```bash
python3 tester.py --parallel --workers 5 --delay-start 0.8
```

---

## 6. Wait for a Specific Selector

```bash
python3 tester.py --wait-selector "#form-container"
```

---

## 7. Change Page Timeout

```bash
python3 tester.py --timeout 50000
```

---

# 📊 Example Output

```
[SEQ] Attempt 1/5 (new trace_id generated)...
[OK] idx=1 http=200 trace=cli-123 msg=HTTP 200, success marker found
snippet: <html> Thank You ...
```

---

# 🔐 Legal & Ethical Notice

This tool **is allowed** for:

- ✔️ Internal QA  
- ✔️ Load testing on your own infrastructure  
- ✔️ Research in authorized labs  
- ✔️ Security auditing with explicit permission  

This tool **must NOT** be used for:

- ❌ Manipulating votes  
- ❌ Spamming forms  
- ❌ Bypassing protections  
- ❌ Attacking third‑party systems  

---


# Disclaimer 🛑

⚠️ **Warning:** This content is for educational purposes only.

This repository and its contents are provided for educational, research, and learning purposes only.

- The material shown — including scripts, commands, and examples — is intended to demonstrate concepts and techniques in a controlled and authorized environment.

- Do not use this material to perform illegal, unauthorized, or harmful activities against networks, systems, or people.

The author accepts no responsibility for any damage, loss, misuse, unauthorized access, legal consequences, or incidents that result from the use of this content. By using this material you agree that you do so at your own risk and that you have the necessary permissions to test or run the procedures described here.

- If you plan to practice on a network or device you do not own, obtain explicit written permission from the owner before proceeding.

## Recommendations

- Use isolated lab environments (virtual machines, test networks) for experimentation.

- Respect applicable laws and your organization’s policies.

- If you have legal or ethical doubts, consult a qualified professional.


---

## Author

This project was developed by **xrl3y**.

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">


## License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

