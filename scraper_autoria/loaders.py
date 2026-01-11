import logging

logger = logging.getLogger(__name__)


def TakeSecond(value):
    """Бере другий елемент зі списку (індекс 1)"""
    # Перевіряємо, чи це список і чи є в ньому хоча б 2 елементи
    if value and len(value) >= 2:
        return value[1]
    # Fallback: якщо елемент всього один, повертаємо його (або None, залежно від логіки)
    return value[0] if value else None


def clean_value(value):
    """Cleans values of extra spaces"""
    if value:
        return value.strip()
    return value


def choose_price(values):
    """
    values: a list of strings, for example
      [“21,000 €”, “38,500”, “1,966,785”]
    or
      [“38500”, “...”]
    In the first case, it should return the second element (the dollar amount without the sign),
    in the second case, the first (since it is already the dollar amount without the sign).
    """
    if not values:
        return None
    first, *rest = values
    if '$' in first:
        return first.strip()
    if rest:
        return rest[0].strip()
    return first.strip()


def clean_price(value):
    """
    Cleans the string of currency symbols and spaces, returns int.
    “47 154 $” -> 47154
    “1 966 785 грн” -> 1966785
    """
    if not value:
        return None
    s = str(value).replace('$', '').replace('грн', '').strip()
    import re
    digits = re.sub(r'[^\d]', '', s)
    return int(digits) if digits else None


def clean_odometer(value):
    """
    Converts mileage from thousands of kilometres to kilometres
    “95 thousand km” -> 95,000
    """
    if not value:
        return None
    # Extract the number from the beginning of the string
    import re
    numbers = re.findall(r'\d+', str(value))
    if numbers:
        return int(numbers[0]) * 1000
    return None


def clean_image_count(value):
    """
    Очищає кількість зображень.
    Працює і для рядків "1 з 13", і просто "31".
    """
    if not value:
        return None
        # Видаляємо все, крім цифр, щоб VIN-код не заважав, якщо він випадково попаде
        # Але VIN теж містить цифри, тому тут важливо, що TakeSecond візьме саме 2-й елемент
    import re
    numbers = re.findall(r'\d+', str(value))

    if len(numbers) >= 2:
        return int(numbers[1])
    elif len(numbers) == 1:
        return int(numbers[0])
    return None


def clean_car_number(value):
    """Cleans the number plate of unnecessary characters"""
    if not value:
        return None
    # Remove extra spaces and characters
    return value.strip().upper()


def clean_car_vin(value):
    """Clears VIN code"""
    if not value:
        return None

    # The VIN code must be 17 characters long.
    cleaned = value.strip().upper()
    if len(cleaned) == 17:
        return cleaned
    return cleaned  # Returns it as is, even if the length is not 17.


def clean_username(value):
    """Clears the user name"""
    if not value:
        return None
    # Remove extra spaces and line break characters
    return value.strip().replace('\n', ' ').replace('\r', '')


def format_phone_number(phone):
    """
    Formats the phone number into international format
    Example: (097) 1234567 -> 380971234567
    """
    if not phone:
        return None

    # Remove all non-digital characters
    import re
    digits = re.sub(r'\D', '', str(phone))
    # If the number starts with 0, replace it with 380.
    if digits.startswith('0'):
        return int('38' + digits)
    # If the number starts with 380, leave it as it is.
    elif digits.startswith('380'):
        return int(digits)
    # If the number is short (less than 9 digits), we assume that it is a local number.
    elif len(digits) < 9:
        return int('380' + digits[-9:])
    # In other cases, we return the numbers as they are.
    return int(digits)


def clean_phone_list(value):
    """
    Processes a list of phone numbers and returns the best option
    """
    if not value:
        return None

    if isinstance(value, list):
        # Filter empty and invalid numbers
        valid_phones = []
        for phone in value:
            if phone and isinstance(phone, str):
                phone = phone.strip()
                if phone and phone not in ['Phone not available', 'Phone not found', 'Not available']:
                    # Checking whether it contains numbers
                    import re
                    if re.search(r'\d', phone):
                        # Format the number after verification
                        formatted_phone = format_phone_number(phone)
                        valid_phones.append(formatted_phone)

        return valid_phones
    else:
        return format_phone_number(value)