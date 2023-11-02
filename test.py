from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # Launch a new browser
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            color_scheme="dark",
        )

        # Set the provided cookies
        cookies = [
            {
                "name": "USER",
                "value": "eyJwcmVmcyI6eyJ0b3BDb250ZW50RGlzbWlzc2FsVGltZSI6MCwiZ2xvYmFsVGhlbWUiOiJSRURESVQiLCJuaWdodG1vZGUiOnRydWUsImNvbGxhcHNlZFRyYXlTZWN0aW9ucyI6eyJmYXZvcml0ZXMiOmZhbHNlLCJtdWx0aXMiOmZhbHNlLCJtb2RlcmF0aW5nIjpmYWxzZSwic3Vic2NyaXB0aW9ucyI6ZmFsc2UsInByb2ZpbGVzIjpmYWxzZX0sInRvcENvbnRlbnRUaW1lc0Rpc21pc3NlZCI6MH19",
                "domain": ".reddit.com",
                "path": "/"
            },
            {
                "name": "eu_cookie",
                "value": "{%22opted%22:true%2C%22nonessential%22:false}",
                "domain": ".reddit.com",
                "path": "/"
            }
        ]

        # Add the cookies to the page
        context.add_cookies(cookies)

        # Open a new page
        page = browser.new_page()

        # Navigate to Reddit
        page.goto("https://www.reddit.com/login", timeout=0)
        page.wait_for_load_state()

        page.locator('[name="username"]').fill(
            "foxnewbie"
        )
        page.locator('[name="password"]').fill(
            "G@briel123"
        )
        page.locator("button[class$='m-full-width']").click()
        page.wait_for_timeout(5000)

        page.wait_for_load_state()
        # Get the thread screenshot
        page.goto("https://www.reddit.com/r/ireland/comments/17l92fv/costa_must_be_punished_for_the_absolutely_dire/", timeout=0)
        page.wait_for_load_state()
        page.wait_for_timeout(5000)

        # Close the browser
        browser.close()

if __name__ == "__main__":
    run()
