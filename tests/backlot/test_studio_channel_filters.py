"""Studio channel-filter contract using synthetic API responses only."""
import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright

from tests.backlot.test_ui_bug_bash import staged_backlot_server


def test_studio_restores_historical_channel_filters_and_payload(staged_backlot_server):
    calls = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 2048, "height": 1152})

        def api(route):
            path = route.request.url.split("?", 1)[0]
            if route.request.method == "POST" and path.endswith("/api/research/channels"):
                calls.append(route.request.post_data_json)
                return route.fulfill(json={
                    "result_type": "channels", "source": "synthetic fixture",
                    "retrieved_at": "2026-11-27T00:00:00Z", "results": [],
                })
            responses = {
                "/api/health": {"ok": True},
                "/api/studio/identity": {"restart_required": False},
                "/api/studio/bootstrap": {"projects": []},
                "/api/studio/storage": {"available": True},
                "/api/studio/editor/capabilities": {"commands": []},
                "/api/studio/editor/projects": [],
                "/api/research/channels/configuration": {"configured": True},
                "/api/research/channels/status": {"configured": True},
            }
            return route.fulfill(json=responses.get(path, {}))

        page.route("**/api/**", api)
        page.goto(staged_backlot_server + "/studio#channels")
        page.locator("#channel-filter-open").click()

        # Historical validation: matching-publication discovery requires a date.
        page.locator('[name="published_within"]').select_option("any")
        page.locator("#channel-filter-form button[type=submit]").click()
        assert "fecha reciente" in page.locator("#channel-filter-error").inner_text()

        page.locator('[name="published_within"]').select_option("month")
        page.locator('[name="sample_size"]').select_option("5")
        page.locator('[name="min_matching_publications"]').fill("2")
        page.locator('[name="min_views"]').fill("1000")
        page.locator('[name="max_views"]').fill("500000")
        page.locator('[name="language"]').select_option("es")
        page.locator('[name="country"]').fill("mx")
        page.locator("#channel-filter-form button[type=submit]").click()
        page.locator("#channel-query").fill("fútbol femenino")
        with page.expect_response(
            lambda response: response.url.endswith("/api/research/channels")
            and response.request.method == "POST"
        ):
            page.locator("#channel-submit").click()

        assert len(calls) == 1
        assert calls[0] == {
            "query": "fútbol femenino",
            "pages": 1,
            "filters": {
                "sample_size": 5,
                "published_within": "month",
                "discovery_mode": "recent_publications",
                "sort_by": "matching_publication_views",
                "content_type": "any",
                "min_matching_publications": 2,
                "min_views": 1000,
                "max_views": 500000,
                "language": "es",
                "country": "MX",
            },
        }
        browser.close()
