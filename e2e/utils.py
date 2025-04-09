import re

from . import AUTH_PROXY_URL, UAA_BASE_URL


def log_in(user, page, start_at):
    # go to auth proxy
    page.goto(start_at)

    # accept the monitoring notice
    agree_continue_button = page.get_by_text("AGREE AND CONTINUE")
    agree_continue_button.wait_for()
    agree_continue_button.click()

    # select the cloud.gov IdP
    cloud_gov_idp_button = page.get_by_role("link", name="cloud.gov")
    cloud_gov_idp_button.wait_for()
    cloud_gov_idp_button.click()

    username_field = page.get_by_label("Email address")
    password_field = page.get_by_label("Password")
    username_field.wait_for()
    password_field.wait_for()
    username_field.fill(user.username)
    password_field.fill(user.password)

    login_button = page.get_by_text("Login")
    login_button.wait_for()
    login_button.click()

    totp_field = page.locator("css=input[id='j_tokenNumber']")
    totp_field.wait_for()
    totp_field.fill(user.totp.now())

    login_button = page.get_by_text("Login")
    login_button.wait_for()
    login_button.click()

    # wait for OAuth authorize page or auth proxy page
    page.wait_for_url(re.compile(f"({AUTH_PROXY_URL}|{UAA_BASE_URL})"))

    # if OAuth authorize page, then authorize the application
    if "/authorize?" in page.url:
        # first time using this app with this user
        authorize_button = page.get_by_text("Authorize")
        authorize_button.wait_for()
        authorize_button.click()
