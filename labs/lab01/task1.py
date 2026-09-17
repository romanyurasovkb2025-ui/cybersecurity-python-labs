"""Завдання 1: Комплексний аналізатор надійності паролів."""

import os
import random
import string
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def evaluate_password_strength(
    password: str,
    criteria: dict,
    forbidden: set,
    all_passwords: list,
) -> str:
    """Оцінює рівень стійкості пароля згідно з варіантом."""
    min_len = criteria["min_length"]

    if password in forbidden or len(password) < min_len:
        return "Заборонений"

    has_digit = any(c.isdigit() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_special = any(c in string.punctuation for c in password)
    has_lower = any(c.islower() for c in password)

    all_criteria_met = has_digit and has_upper and has_special and has_lower
    any_criteria_met = has_digit or has_upper or has_special or has_lower

    is_unique = all_passwords.count(password) == 1

    if all_criteria_met and len(password) >= min_len + 4 and is_unique:
        return "Дуже сильний"
    if all_criteria_met and len(password) < min_len + 4:
        return "Сильний"
    if any_criteria_met and not all_criteria_met:
        return "Середній"
    if any_criteria_met:
        return "Слабкий"

    return "Заборонений"


def run_task1():
    """Головна функція виконання Завдання 1."""
    print("=" * 60)
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print("=" * 60)

    passwords = [
        "Digital@F0r3nsics",
        "plain",
        "Encrypt10n@Key",
        "member",
        "Security@Audit2023",
        "regular",
        "Hack3r@D3fense",
        "ordinary",
        "Threat@Intel",
        "usual",
    ]
    criteria = {
        "min_length": 8,
        "require_digits": True,
        "require_upper": True,
        "require_special": True,
    }
    forbidden_passwords = {
        "plain",
        "member",
        "regular",
        "ordinary",
        "usual",
        "user",
    }

    random_indices = [random.randint(0, len(passwords) - 1) for _ in range(3)]
    for idx in random_indices:
        passwords.append(passwords[idx])

    print(f"\n{'Пароль':<25} | {'Результат аналізу'}")
    print("-" * 50)
    for pwd in passwords:
        strength = evaluate_password_strength(
            pwd, criteria, forbidden_passwords, passwords
        )
        print(f"{pwd:<25} | {strength}")


if __name__ == "__main__":
    run_task1()
