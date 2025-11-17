#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlled testing example using a real browser (Playwright).

- Executes any JS challenge on the page (browser handles it).
- Sends a POST request from the browser context using fetch().
- Supports sequential or parallel execution via multiprocessing.
- Each attempt generates a trace_id for log correlation.

⚠ FOR CONTROLLED / STAGING ENVIRONMENTS ONLY. DO NOT USE ON THIRD-PARTY SYSTEMS. ⚠
"""

import argparse
import random
import time
import uuid
import json
from typing import Dict, Optional, Any, List
from multiprocessing import Pool


# ==========================
# TEST CONFIGURATION
# ==========================

# Base URL of your testing environment (fill in privately)
BASE = "https://example.test"  # <- REPLACE IN PRIVATE

# Page that contains the form or challenge
PAGE_URL = BASE + "/test-page/"  # <- REPLACE IN PRIVATE

# AJAX/HTTP endpoint that processes the form
AJAX_URL_BASE = BASE + "/ajax-endpoint"  # <- REPLACE IN PRIVATE

# Base payload example (use your real payload in your private environment)
BASE_PAYLOAD = {
    "field_option": "value_option",
    "screen": "submit",
    "formId": "123",
    "action": "submit",
}

# Marker used to heuristically detect a successful response
SUCCESS_MARKER = "thank you"


# Browser-like headers
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Referer": PAGE_URL,
}


# ==========================
# UTILITIES
# ==========================

def build_payload_with_trace(trace: str, nonce: Optional[str]) -> List[tuple]:
    """
    Build a list of (key, value) pairs to be appended into FormData.

    It clones BASE_PAYLOAD and adds:
    - trace_id
    - nonce (if required by the tested application)
    """
    p = BASE_PAYLOAD.copy()
    p["trace_id"] = trace
    if nonce:
        p["_nonce"] = nonce

    return list(p.items())


# ==========================
# WORKER FUNCTION
# ==========================

def worker_send(args_tuple) -> Dict[str, Any]:
    """
    Runs inside a separate process so multiple Playwright instances
    can run safely in parallel.

    args_tuple = (index, headless, wait_for_selector, timeout_ms)
    """
    index, headless, wait_for_selector, timeout_ms = args_tuple

    # Import Playwright inside the worker
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except Exception as e:
        return {
            "index": index,
            "ok": False,
            "message": f"Playwright import error: {e}",
            "http_status": None,
            "trace": None,
        }

    trace = f"cli-{uuid.uuid4()}"
    result = {
        "index": index,
        "trace": trace,
        "ok": False,
        "http_status": None,
        "message": None,
        "response_snippet": None,
    }

    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=headless)
            context = browser.new_context(user_agent=BROWSER_HEADERS["User-Agent"])
            page = context.new_page()

            # Open the testing page
            try:
                page.goto(PAGE_URL, wait_until="networkidle", timeout=timeout_ms)
            except PlaywrightTimeout:
                try:
                    page.goto(PAGE_URL, wait_until="load", timeout=timeout_ms)
                except Exception as e:
                    result["message"] = f"Failed to load page: {e}"
                    browser.close()
                    return result

            # Extract possible nonce if your app requires it
            nonce = None
            try:
                el = page.query_selector('input[name="_nonce"]')
                if el:
                    nonce = el.get_attribute("value")

                # Optional: wait for a specific selector (e.g., form container)
                if wait_for_selector:
                    try:
                        page.wait_for_selector(wait_for_selector, timeout=6000)
                    except PlaywrightTimeout:
                        pass
            except Exception:
                pass

            # Prepare payload
            form_pairs = build_payload_with_trace(trace, nonce)
            js_payload = json.dumps(form_pairs)
            ajax_url_with_trace = f"{AJAX_URL_BASE}?trace_id={trace}"

            # JavaScript executed inside the browser
            fetch_script = f"""
                (async () => {{
                    try {{
                        const pairs = {js_payload};
                        const fd = new FormData();
                        for (const [k, v] of pairs) {{
                            fd.append(k, v);
                        }}
                        const resp = await fetch("{ajax_url_with_trace}", {{
                            method: "POST",
                            body: fd,
                            credentials: "same-origin",
                            headers: {{
                                "X-Requested-With": "XMLHttpRequest"
                            }}
                        }});
                        const text = await resp.text();
                        return {{
                            status: resp.status,
                            ok: resp.ok,
                            text: text.slice(0, 2000)
                        }};
                    }} catch (e) {{
                        return {{ error: String(e) }};
                    }}
                }})();
            """

            fetch_result = page.evaluate(fetch_script)

            # Handle result
            if isinstance(fetch_result, dict):
                if "error" in fetch_result:
                    result["message"] = f"Fetch error: {fetch_result['error']}"
                else:
                    result["http_status"] = fetch_result.get("status")
                    snippet = fetch_result.get("text")
                    result["response_snippet"] = snippet

                    if fetch_result.get("status") == 200:
                        if SUCCESS_MARKER.lower() in (snippet or "").lower():
                            result["ok"] = True
                            result["message"] = "HTTP 200 and success marker found."
                        else:
                            result["ok"] = True
                            result["message"] = "HTTP 200, no success marker found."
                    else:
                        result["message"] = f"HTTP {fetch_result.get('status')}"
            else:
                result["message"] = f"Unexpected fetch result: {fetch_result!r}"

            browser.close()

    except Exception as e:
        result["message"] = f"Unhandled exception: {e}"

    return result


# ==========================
# CONTROLLERS
# ==========================

def run_sequential(reps: int, headless: bool, delay: float,
                   wait_selector: Optional[str], timeout_ms: int) -> List[Dict[str, Any]]:
    """
    Run attempts sequentially.
    """
    out = []
    for i in range(1, reps + 1):
        print(f"[SEQ] Attempt {i}/{reps} (new trace_id will be generated)...")
        res = worker_send((i, headless, wait_selector, timeout_ms))
        out.append(res)
        status = "OK" if res.get("ok") else "ERROR"
        print(f"[{status}] idx={res['index']} http={res.get('http_status')} "
              f"trace={res.get('trace')} msg={res.get('message')}")
        if res.get("response_snippet"):
            print("  snippet:", res["response_snippet"][:300].replace("\n", " "))

        if i < reps:
            time.sleep(delay + random.uniform(0, delay * 0.3))

    return out


def run_parallel(reps: int, workers: int, headless: bool, delay_between_starts: float,
                 wait_selector: Optional[str], timeout_ms: int) -> List[Dict[str, Any]]:
    """
    Run attempts in parallel using multiprocessing.
    """
    args = [(i, headless, wait_selector, timeout_ms) for i in range(1, reps + 1)]
    out = []

    print(f"[PAR] Dispatching {reps} attempts using {workers} processes...")

    with Pool(processes=workers) as pool:
        results = pool.imap_unordered(worker_send, args)

        for res in results:
            out.append(res)
            status = "OK" if res.get("ok") else "ERROR"
            print(f"[{status}] idx={res['index']} http={res.get('http_status')} "
                  f"trace={res.get('trace')} msg={res.get('message')}")

            if res.get("response_snippet"):
                print("  snippet:", res["response_snippet"][:300].replace("\n", " "))

            time.sleep(delay_between_starts + random.uniform(0, delay_between_starts * 0.25))

    out.sort(key=lambda x: x.get("index", 0))
    return out


# ==========================
# CLI
# ==========================

def main():
    parser = argparse.ArgumentParser(
        description="Playwright-based test script for controlled environments."
    )
    parser.add_argument("--reps", type=int, default=1, help="Number of attempts.")
    parser.add_argument("--parallel", action="store_true", help="Run in parallel mode.")
    parser.add_argument("--workers", type=int, default=2, help="Number of worker processes.")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Base delay between attempts (sequential mode).")
    parser.add_argument("--delay-start", type=float, default=0.6,
                        help="Delay between process starts (parallel mode).")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode.")
    parser.add_argument("--wait-selector", type=str, default=None,
                        help="Optional selector to wait for after loading the page.")
    parser.add_argument("--timeout", type=int, default=30000,
                        help="Page navigation timeout (ms).")

    args = parser.parse_args()

    print("=== Playwright Controlled Tester ===")
    print(f"reps={args.reps} parallel={args.parallel} workers={args.workers} "
          f"delay={args.delay} headless={args.headless}")

    if args.parallel:
        results = run_parallel(
            args.reps, args.workers, args.headless, args.delay_start,
            args.wait_selector, args.timeout
        )
    else:
        results = run_sequential(
            args.reps, args.headless, args.delay,
            args.wait_selector, args.timeout
        )

    ok_count = sum(1 for r in results if r.get("ok"))

    print("\n=== FINAL SUMMARY ===")
    print(f"Total attempts: {len(results)}, success: {ok_count}, failed: {len(results) - ok_count}")

    for r in results:
        print(f"#{r['index']} ok={r.get('ok')} http={r.get('http_status')} "
              f"trace={r.get('trace')} msg={r.get('message')}")


if __name__ == "__main__":
    main()
