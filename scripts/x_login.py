from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

from playwright.async_api import async_playwright

from app.config import get_settings

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined,
});
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'languages', {
  get: () => ['en-US', 'en'],
});
Object.defineProperty(navigator, 'plugins', {
  get: () => [1, 2, 3, 4, 5],
});
"""


async def main() -> None:
    settings = get_settings()
    storage_state_path = Path(settings.x_storage_state_path)
    storage_state_path.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=settings.user_agent,
            locale="en-US",
            viewport={"width": 1440, "height": 960},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
        )
        await context.add_init_script(STEALTH_INIT_SCRIPT)
        page = await context.new_page()

        print("Opening X in a real browser window.")
        print("If the direct login flow is blocked, open x.com manually in that window and sign in there.")
        try:
            await page.goto(settings.x_login_url, wait_until="domcontentloaded")
            await asyncio.to_thread(input, "Press Enter after the X session is logged in and ready...")
            await context.storage_state(path=str(storage_state_path))
            print(f"Saved authenticated X session to {storage_state_path}")
        except KeyboardInterrupt:
            print("\nLogin helper cancelled before saving the session.")
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
