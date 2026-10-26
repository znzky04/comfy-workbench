"""Headless desktop/mobile verification against an already running local studio."""

import argparse
import json
import os
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--generate", action="store_true", help="Submit one real two-image job")
parser.add_argument("--reference-image", type=Path, required=True, help="Existing local reference image")
args = parser.parse_args()
artifacts = Path("runs/browser-check") / uuid.uuid4().hex[:12]
artifacts.mkdir(parents=True, exist_ok=True)
browser_temp = Path("runs/browser-temp").resolve()
browser_temp.mkdir(parents=True, exist_ok=True)
os.environ["TEMP"] = str(browser_temp)
os.environ["TMP"] = str(browser_temp)
errors = []

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8199")
    page.wait_for_load_state("networkidle")
    page.locator(".art-card").first.wait_for()
    assert page.title() == "星夜绘图室 · ComfyUI Agent Studio"
    assert page.locator("#workflow option").count() == 5
    assert page.request.post("http://127.0.0.1:8199/api/jobs", data={}).status == 403
    page.get_by_role("button", name="原创角色", exact=True).click()
    assert page.locator(".art-card").count() >= 3
    page.locator(".art-card").first.click()
    assert page.locator("#artifact-dialog").is_visible()
    assert Path(page.locator("#dialog-path").input_value()).is_absolute()
    page.get_by_role("button", name="关闭 ×").click()
    page.get_by_role("button", name="全部记录", exact=True).click()
    page.evaluate("document.activeElement.blur(); window.scrollTo(0,0)")
    page.screenshot(path=str(artifacts / "desktop.png"), full_page=True)
    page.select_option("#workflow", "larkie.img2img.v1")
    page.locator("#reference-box").wait_for(state="visible")
    with page.expect_response(lambda r: r.url.endswith("/api/uploads") and r.status == 200):
        page.locator("#reference").set_input_files(
            str(args.reference_image.resolve())
        )
    page.wait_for_function(
        "document.querySelector('#reference-status').textContent.includes('已上传')"
    )
    if args.generate:
        page.select_option("#workflow", "anima.standard.v1")
        page.wait_for_function(
            "document.querySelector('#workflow-hint').textContent.includes('文字')"
        )
        page.locator("#prompt").fill(
            "An original adult ocean astrologer, long wavy teal hair, layered ceremonial robes, "
            "coral staff, moonlit sea and stars, full body anime illustration, elegant composition."
        )
        page.locator("#width").fill("512")
        page.locator("#height").fill("768")
        page.select_option("#count", "2")
        page.locator(".advanced summary").click()
        page.locator("#seed").fill("0")
        page.locator("#steps").fill("16")
        with page.expect_response(
            lambda r: r.url.endswith("/api/jobs") and r.request.method == "POST", timeout=20000
        ) as submission:
            page.get_by_role("button", name="开始生成").click()
        job = submission.value.json()
        assert submission.value.status == 202, job
        job_id = job["job_id"]
        page.wait_for_function(
            "document.querySelector('#job-title').textContent === '已完成'", timeout=180000
        )
        completed = page.request.get(f"http://127.0.0.1:8199/api/jobs/{job_id}").json()
        assert len(completed["artifacts"]) == 2, completed
        assert completed["client"] == "studio"
        assert [r["seed"] for r in completed["resolved_parameters"]["runs"]] == [0, 1]
        print(
            json.dumps(
                {"live_job_id": job_id, "artifacts": completed["artifacts"]}, ensure_ascii=False
            )
        )
        page.screenshot(path=str(artifacts / "desktop-live.png"), full_page=True)
    mobile = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    mobile.on("pageerror", lambda error: errors.append(str(error)))
    mobile.goto("http://127.0.0.1:8199")
    mobile.wait_for_load_state("networkidle")
    mobile.locator(".art-card").first.wait_for()
    assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert mobile.get_by_role("button", name="开始生成").is_visible()
    mobile.screenshot(path=str(artifacts / "mobile.png"), full_page=True)
    browser.close()
assert not errors, errors
print("PASS desktop, mobile, filters, dialog, upload, CSRF, no horizontal overflow, zero JS errors")
print("SCREENSHOTS", artifacts.resolve())
