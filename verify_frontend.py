import os
import time
from playwright.sync_api import sync_playwright, expect

def verify_file_picker():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to the app
        # Since nicegui starts on a random port usually or 8080, let's check logs or assume 8080
        # NiceGUI default is 8080.
        page.goto("http://localhost:8080")

        # Wait for title
        expect(page).to_have_title("Audiopub")

        # Wait for the browse button. We added an icon "folder_open" to the button.
        # Let's find the button by the icon or by its parent structure.
        # We have two browse buttons. Let's click the first one (EPUB browse).

        # The button has icon 'folder_open' and classes 'aspect-square'.
        # We can try to find the button that contains the icon.

        # In Quasar (NiceGUI), icons are usually inside an <i> tag with class q-icon.
        # The button is a <button>.

        # Let's wait for the page to load completely
        page.wait_for_selector('text=SOURCE FILE')

        # Click the first folder_open button
        # We can use get_by_role('button') and filter.
        buttons = page.get_by_role("button").all()
        browse_btn = None
        for btn in buttons:
            if "folder_open" in btn.inner_html():
                browse_btn = btn
                break

        if not browse_btn:
            print("Browse button not found!")
            page.screenshot(path="debug_no_btn.png")
            return

        browse_btn.click()

        # Wait for dialog to appear.
        # The dialog has a title bar with the current path (initially '.' or cwd).
        # We look for the "close" button or "folder_open" icon in the dialog header.

        # Wait for the dialog content to be visible.
        # Our dialog has a card with class w-[600px].
        page.wait_for_selector('.w-\[600px\]')

        # Take screenshot
        os.makedirs("/home/jules/verification", exist_ok=True)
        screenshot_path = "/home/jules/verification/file_picker_dialog.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    # Give the server a moment to start if it was just launched
    time.sleep(3)
    verify_file_picker()
