from .selectors import SELECTORS
from pathlib import Path
from datetime import datetime
import json


def _debug_dir(provider: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path("runtime/evidence/web_ai") / provider / ts
    path.mkdir(parents=True, exist_ok=True)
    return path


class PromptSender:
    async def send(
        self,
        page,
        provider: str,
        prompt: str,
        attachments: list[str] | None = None,
        debug: bool = False,
    ):
        errors: list[str] = []
        used_input_strategy = ""
        used_send_strategy = ""
        sel = SELECTORS.get(provider, SELECTORS["chatgpt"])["input"]
        locator = page.locator(sel).last
        if debug:
            out = _debug_dir(provider)
            await page.screenshot(path=str(out / "screenshot_before_send.png"), full_page=True)
            (out / "dom_excerpt.html").write_text(
                (await page.locator("body").evaluate("el => el.outerHTML"))[:250000],
                encoding="utf-8",
            )

        async def visible_click_fill():
            await locator.scroll_into_view_if_needed(timeout=10000)
            await locator.wait_for(state="visible", timeout=10000)
            await locator.click(timeout=10000)
            await locator.fill(prompt, timeout=10000)

        async def force_click_keyboard_type():
            await locator.scroll_into_view_if_needed(timeout=10000)
            await locator.click(force=True, timeout=10000)
            await page.keyboard.press("Meta+A")
            await page.keyboard.type(prompt, delay=2)

        async def js_focus_insert_text():
            handle = await locator.element_handle(timeout=10000)
            if handle is None:
                raise RuntimeError("input element handle unavailable")
            await handle.evaluate(
                """(el) => {
                    el.scrollIntoView({block: 'center', inline: 'nearest'});
                    el.focus();
                    if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                        el.value = '';
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                    } else if (el.isContentEditable) {
                        el.textContent = '';
                        el.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'deleteContent'}));
                    }
                }"""
            )
            await page.keyboard.insert_text(prompt)

        async def clipboard_paste():
            await page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=page.url)
            await page.evaluate(
                "text => navigator.clipboard.writeText(text)",
                prompt,
            )
            await locator.click(force=True, timeout=10000)
            await page.keyboard.press("Meta+V")

        for name, action in [
            ("visible_click_fill", visible_click_fill),
            ("force_click_keyboard_type", force_click_keyboard_type),
            ("js_focus_insert_text", js_focus_insert_text),
            ("clipboard_paste", clipboard_paste),
        ]:
            try:
                await action()
                used_input_strategy = name
                break
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        if not used_input_strategy:
            await self._save_failure_artifacts(page, provider, "send_input_failed", errors)
            raise RuntimeError("Unable to input prompt; " + " | ".join(errors[-3:]))

        send_sel = SELECTORS.get(provider, SELECTORS["chatgpt"])["send"]
        send_errors: list[str] = []

        for name, action in [
            ("button_click", lambda: page.locator(send_sel).last.click(timeout=5000)),
            ("button_force_click", lambda: page.locator(send_sel).last.click(force=True, timeout=5000)),
            ("enter", lambda: page.keyboard.press("Enter")),
            ("meta_enter", lambda: page.keyboard.press("Meta+Enter")),
        ]:
            try:
                await action()
                used_send_strategy = name
                break
            except Exception as exc:
                send_errors.append(f"{name}: {exc}")
        if not used_send_strategy:
            await self._save_failure_artifacts(page, provider, "send_button_failed", send_errors)
            raise RuntimeError("Unable to send prompt; " + " | ".join(send_errors[-3:]))

        if debug:
            out = _debug_dir(provider)
            await page.screenshot(path=str(out / "screenshot_after_send.png"), full_page=True)
            (out / "candidate_selectors.json").write_text(
                json.dumps(
                    {
                        "input": sel,
                        "send": send_sel,
                        "used_input_strategy": used_input_strategy,
                        "used_send_strategy": used_send_strategy,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        return {
            "send_success": True,
            "used_input_strategy": used_input_strategy,
            "used_send_strategy": used_send_strategy,
            "prompt_timestamp": datetime.now().isoformat(),
        }

    async def _save_failure_artifacts(self, page, provider: str, stage: str, errors: list[str]):
        out = _debug_dir(provider)
        try:
            await page.screenshot(path=str(out / "screenshot.png"), full_page=True)
        except Exception:
            pass
        try:
            (out / "dom_excerpt.html").write_text(
                (await page.locator("body").evaluate("el => el.outerHTML"))[:250000],
                encoding="utf-8",
            )
        except Exception:
            pass
        (out / "metadata.json").write_text(
            json.dumps(
                {
                    "provider": provider,
                    "stage": stage,
                    "errors": errors,
                    "created_at": datetime.now().isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
