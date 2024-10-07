import telegram_gateway
from dearpygui import dearpygui

gateway = None

dearpygui.create_context()
dearpygui.create_viewport(title='Telegram Gateway API')

def on_api_key_input(button: int | str, api_key: str, window: int | str) -> None:
    global gateway
    dearpygui.delete_item(window)
    gateway = telegram_gateway.TelegramGateway(api_key)
    main_menu()

def show_message(title: str, text: str) -> None:
    with dearpygui.window(label=title, modal=True) as window:
        dearpygui.add_text(text)
        dearpygui.add_button(label="Close", callback=lambda x: dearpygui.delete_item(window))
    dearpygui.split_frame()
    size = dearpygui.get_item_rect_size(window)
    dearpygui.set_item_pos(window, [dearpygui.get_viewport_width() // 2 - size[0] // 2, dearpygui.get_viewport_height() // 2 - size[1] // 2])

send_ability_codes: dict[str, str] = dict()

def revoke_code(request_id: str, window: int | str) -> None:
    dearpygui.delete_item(window)
    try:
        gateway.revokeVerificationMessage(request_id)
        main_menu()
        show_message("Success", "The code was revoked.")
    except:
        main_menu()
        show_message("Error", "Something went wrong while revoking the code.")

def check_code(request_id: str, window: int | str, code: str) -> None:
    dearpygui.hide_item(window)
    try:
        result = gateway.checkVerificationStatus(request_id, code=code)
        if result.verification_status.status != telegram_gateway.enums.VerificationResult.CODE_INVALID:
            dearpygui.delete_item(window)
            main_menu()
        else:
            dearpygui.show_item(window)
        show_message("Code checked", f"Status: {result.verification_status.status.replace('_', ' ').capitalize()}")
    except ValueError as e:
        dearpygui.show_item(window)
        show_message("Error", " ".join(e.args))
    except RuntimeError as e:
        dearpygui.show_item(window)
        
        if e.args[0].startswith("FLOOD_WAIT_"):
            show_message("Error", f"You're sending requests too fast. Retry after {e.args[0].removeprefix('FLOOD_WAIT_')} seconds.")
        else:
            show_message("Error", " ".join(e.args))

def send_code(phone: str, window: int | str) -> None:
    dearpygui.delete_item(window)
    try:
        result = gateway.sendVerificationMessage(phone, code_length=8)
    except ValueError as e:
        main_menu()
        show_message("Error", " ".join(e.args))
    except RuntimeError as e:
        main_menu()
        
        if e.args[0].startswith("FLOOD_WAIT_"):
            show_message("Error", f"You're sending requests too fast. Retry after {e.args[0].removeprefix('FLOOD_WAIT_')} seconds.")
        else:
            show_message("Error", " ".join(e.args))
    else:
        with dearpygui.window(label="Code sent") as window:
            dearpygui.set_primary_window(window, True)
            dearpygui.add_text("The code was sent. Enter the code into the input field and press Validate, or revoke it.")
            dearpygui.add_button(label="Revoke code", callback=lambda x: revoke_code(result.request_id, window))
            code = dearpygui.add_input_text()
            dearpygui.add_button(label="Check code", callback=lambda x: check_code(result.request_id, window, dearpygui.get_value(code)))

def check_send_ability(phone: str, window: int | str) -> None:
    dearpygui.delete_item(window)
    try:
        result = gateway.checkSendAbility(phone)
        send_ability_codes[phone] = result.request_id
        main_menu()
        show_message("Check passed", f"You can send codes to {phone}.")
    except ValueError as e:
        main_menu()
        show_message("Invalid value", " ".join(e.args))
    except RuntimeError as e:
        main_menu()
        if e.args[0].startswith("FLOOD_WAIT_"):
            show_message("Error", f"You're sending requests too fast. Retry after {e.args[0].removeprefix('FLOOD_WAIT_')} seconds.")
        else:
            show_message("Error", " ".join(e.args))

def change_api_key(window: int | str) -> None:
    dearpygui.delete_item(window)
    set_api_key()

def main_menu() -> None:
    global gateway
    with dearpygui.window(label="Telegram Gateway") as window:
        dearpygui.set_primary_window(window, True)
        dearpygui.add_text("Enter the phone number (in E.164 format) to which you'd like to send the code to.")
        dearpygui.add_text("Sending codes to yourself (the one that owns the API key) is free, but sending it to other people is paid.", bullet=True)
        dearpygui.add_text("The same applies to checking the sending ability.", bullet=True)
        phone_input = dearpygui.add_input_text()
        with dearpygui.group(horizontal=True):
            dearpygui.add_button(label="Send code", callback=lambda x: send_code(dearpygui.get_value(phone_input), window))
            dearpygui.add_button(label="Check sending ability", callback=lambda x: check_send_ability(dearpygui.get_value(phone_input), window))
            dearpygui.add_button(label="Change API key", callback=lambda x: change_api_key(window))

def set_api_key():
    with dearpygui.window(label="Set API token") as window:
        dearpygui.set_primary_window(window, True)
        dearpygui.add_text("Please enter your API key from https://gateway.telegram.org/:")
        api_key = dearpygui.add_input_text(password=True)
        dearpygui.add_button(label="Confirm", callback=lambda x: on_api_key_input(x, dearpygui.get_value(api_key), window))

set_api_key()

dearpygui.setup_dearpygui()
dearpygui.show_viewport()
dearpygui.start_dearpygui()
dearpygui.destroy_context()