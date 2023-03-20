import json


def dedent(text: str) -> str:
    """A more lenient version of `textwrap.dedent`."""

    return "\n".join(map(str.strip, text.splitlines())).strip()


def strip_last_occurrence(text: str, text_to_strip: str, strip_remaining_text=False) -> str:
    index = text.rfind(text_to_strip)
    if index != -1:
        stripped_text = text[:index]
        if not strip_remaining_text:
            stripped_text += text[index + len(text_to_strip):]
        return stripped_text
    else:
        return text


def handle_json_error(text, error_code: str):
    match error_code:
        case "Expecting property name enclosed in double quotes":
            return strip_last_occurrence(text, ",")


def json_load(str_json):
    try:
        return json.loads(str_json)
    except json.JSONDecodeError as e:
        print("Repairing JSON.")
        json_error = str(e).split(":")[0]
        fixed_json_string = handle_json_error(str_json, json_error)
        return json.loads(fixed_json_string)
