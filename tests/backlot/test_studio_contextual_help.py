"""Accessible, persistent button help; all API traffic is synthetic/local."""
import pytest
from urllib.parse import urlsplit

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright, expect

from tests.backlot.test_ui_bug_bash import staged_backlot_server


def test_button_help_is_accessible_toggleable_and_persistent(staged_backlot_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2048, "height": 1152})

        def api(route):
            path = urlsplit(route.request.url).path
            responses = {
                "/api/health": {"ok": True},
                "/api/studio/identity": {"restart_required": False},
                "/api/studio/bootstrap": {"projects": []},
                "/api/studio/storage": {"available": True},
                "/api/studio/editor/capabilities": {"commands": []},
                "/api/studio/editor/projects": [],
            }
            return route.fulfill(json=responses.get(path, {}))

        page.route("**/api/**", api)
        page.goto(staged_backlot_server + "/studio#video")
        toggle = page.locator("#context-help-enabled")
        expect(toggle).to_be_checked()

        create = page.locator("#top-new-project")
        original_name = create.inner_text().strip()
        create.focus()
        help_region = page.locator("#studio-button-help")
        expect(help_region).to_be_visible()
        expect(help_region).to_contain_text("carpeta de proyecto")
        assert "studio-button-help" in (create.get_attribute("aria-describedby") or "")
        assert create.inner_text().strip() == original_name
        box = create.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        expect(help_region).to_contain_text("carpeta de proyecto")

        # A button appended after startup receives contextual help too.
        page.locator('.nav-item[data-module="projects"]').click()
        page.evaluate("""() => {
          const button = document.createElement('button');
          button.id = 'dynamic-help-fixture';
          button.textContent = 'Revisar tarjeta';
          document.querySelector('#module-projects').append(button);
        }""")
        dynamic = page.locator("#dynamic-help-fixture")
        expect(dynamic).to_have_attribute("data-context-help-ready", "true")
        dynamic.focus()
        expect(help_region).to_contain_text("Proyectos: Revisar tarjeta")

        # The help uses a reserved topbar slot; it does not cover top actions.
        assert page.evaluate("""() => {
          const a = document.querySelector('#studio-button-help').getBoundingClientRect();
          const b = document.querySelector('.top-actions').getBoundingClientRect();
          return a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom;
        }""")

        page.locator('.nav-item[data-module="settings"]').click()
        toggle = page.locator("#context-help-enabled")
        toggle.uncheck()
        expect(toggle).not_to_be_checked()
        expect(help_region).to_be_hidden()
        assert "studio-button-help" not in (create.get_attribute("aria-describedby") or "")
        expect(create).to_have_accessible_name("Nuevo proyecto")
        assert page.evaluate("localStorage.getItem('openmontage.studio.context-help.v1')") == "false"

        page.reload()
        expect(page.locator("#context-help-enabled")).not_to_be_checked()
        browser.close()
