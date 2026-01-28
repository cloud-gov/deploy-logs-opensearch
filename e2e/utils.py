import re
from playwright.sync_api import expect

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


def switch_tenants(page, tenant="Global"):
    """
    switch to the specified tenant.
    """

    select_tenant_header = page.get_by_role(
        "heading", name="Select your tenant", exact=True
    )
    select_tenant_header.wait_for()

    custom_tenant_checkbox = page.get_by_label("Choose from custom")
    expect(custom_tenant_checkbox).to_be_visible()
    expect(custom_tenant_checkbox).to_be_enabled()

    selected_tenant = page.get_by_role("combobox").get_by_text(tenant, exact=True)

    if not selected_tenant.is_visible():
        open_tenant_options_btn = page.get_by_label("Open list of options")
        open_tenant_options_btn.wait_for()
        open_tenant_options_btn.click()

        tenant_option = page.get_by_role("option", name=tenant)
        tenant_option.wait_for()
        tenant_option.click()

    # submit
    submit_button = page.get_by_text("Confirm")
    submit_button.wait_for()
    submit_button.click()

    # wait for loading screen
    loading_text = page.get_by_text("Loading Cloud.gov Logs")
    loading_text.wait_for()

    # wait for dashboard to finish loading
    dashboards_title = page.get_by_role("heading", name="Dashboards")
    dashboards_title.wait_for()


def open_primary_menu_link(page, menu_link_name):
    # open the hamburger menu
    hamburger_button = page.get_by_label("Toggle primary navigation")
    hamburger_button.wait_for()
    hamburger_button.click()

    menu_link = page.get_by_text(menu_link_name)
    menu_link.wait_for()
    menu_link.click()


def click_contextual_menu_link(page, link_name):
    link = page.locator("#app-wrapper").get_by_role("link", name=link_name, exact=True)
    link.wait_for()
    link.click()


def wait_for_header(page, header_name):
    channels_header = page.get_by_role("heading", name=header_name)
    channels_header.wait_for()


def fill_delete_confirm_placeholder(page):
    delete_confirm_input = page.get_by_placeholder("delete")
    delete_confirm_input.wait_for()
    delete_confirm_input.fill("delete")


def open_actions_menu(page):
    actions_button = page.get_by_role("button", name="Actions", exact=True)
    actions_button.wait_for()
    actions_button.click()


def click_actions_edit_link(page):
    open_actions_menu(page)
    actions_edit_button = page.get_by_role("button", name="Edit", exact=True)
    actions_edit_button.wait_for()
    actions_edit_button.click()


def click_delete_button(page):
    delete_button = page.get_by_role("button", name="Delete", exact=True)
    delete_button.wait_for()
    delete_button.click()


def select_table_item_checkbox(page, item_text):
    checkbox = page.locator("tr").filter(has_text=item_text).get_by_role("checkbox")
    checkbox.wait_for()
    checkbox.click()


def click_table_edit_button(page):
    edit_button = page.get_by_role("button", name="Edit", exact=True).first
    expect(edit_button).to_be_visible()
    expect(edit_button).to_be_enabled()
    edit_button.click()


def click_tab_link(page, link_text):
    link = page.get_by_role("tab", name=link_text)
    link.wait_for()
    link.click()


def wait_for_loading_finished(page):
    expect(page.get_by_label("Loading content")).not_to_be_visible()


def update_rows_per_table(page, rows_option="50 rows"):
    rows_per_page_button = page.get_by_role(
        "button", name=re.compile(r"^Rows per page: [0-9]+$")
    )
    rows_per_page_button.wait_for()
    rows_per_page_button.click()

    fifty_rows_button = page.get_by_role("button", name=rows_option, exact=True)
    fifty_rows_button.wait_for()
    fifty_rows_button.click()


def get_dismiss_toast_notification_buttons(page):
    return page.get_by_label("Dismiss toast")


def wait_and_dismiss_toast_notification(page):
    toast = get_dismiss_toast_notification_buttons(page)
    toast.wait_for()
    toast.click()


def dismiss_toast_notifications(page):
    dismiss_toast_buttons = get_dismiss_toast_notification_buttons(page)
    for i in range(dismiss_toast_buttons.count()):
        if dismiss_toast_buttons.nth(i).is_visible():
            dismiss_toast_buttons.nth(i).click()


def click_save_button(page):
    save_button = page.get_by_role("button", name="Save")
    save_button.wait_for()
    save_button.click()
