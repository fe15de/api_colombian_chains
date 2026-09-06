def get_auth_header(url : str, url_substring : str, timeout_ms : int = 20_000, nav_timeout_ms : int = 60_000) -> str | None:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

    def wanted(request) -> bool:
        return url_substring in request.url and 'authorization' in request.headers

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        # We only need the JS that fires the API call; skip the heavy assets.
        page.route('**/*', lambda route: route.abort()
                   if route.request.resource_type in {'image', 'media', 'font'}
                   else route.continue_())

        try:
            with page.expect_request(wanted, timeout=timeout_ms) as info:
                page.goto(url, wait_until='commit', timeout=nav_timeout_ms)
            return info.value.headers.get('authorization')
        except PlaywrightTimeoutError:
            return None
        finally:
            browser.close()
