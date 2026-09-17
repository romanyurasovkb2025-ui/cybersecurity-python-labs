"""Завдання 2: Багаторівнева система контролю доступу."""


def check_access(
    username: str, resource_name: str, users: dict, resources: list, blocked_users: set
) -> tuple:
    """Перевіряє доступ конкретного користувача до вказаного ресурсу."""
    if username not in users:
        return False, "User not found"
    if username in blocked_users:
        return False, "User is blocked"

    user_info = users[username]
    if not user_info.get("active", False):
        return False, "Account inactive"

    res_level = dict(resources).get(resource_name)
    if res_level is None:
        return False, "Resource not found"

    if user_info.get("clearance", 0) >= res_level:
        return True, ""
    return False, "Insufficient clearance"


def run_task2():
    """Головна функція виконання Завдання 2."""
    users = {
        "cloud_architect": {
            "role": "cloud_security",
            "clearance": 4,
            "department": "Cloud",
            "active": True,
        },
        "devops_engineer": {
            "role": "devops",
            "clearance": 3,
            "department": "DevOps",
            "active": True,
        },
        "qa_tester": {
            "role": "quality_assurance",
            "clearance": 2,
            "department": "QA",
            "active": True,
        },
        "partner_access": {
            "role": "partner",
            "clearance": 2,
            "department": "Partnership",
            "active": True,
        },
        "migrated_user": {
            "role": "migrated",
            "clearance": 1,
            "department": "Migration",
            "active": False,
        },
    }

    resources = [
        ("cloud_configs", 4),
        ("deployment_pipelines", 3),
        ("test_environments", 2),
        ("partner_apis", 2),
        ("infrastructure_code", 4),
        ("shared_resources", 1),
        ("container_registry", 3),
        ("secrets_vault", 4),
        ("build_artifacts", 2),
        ("public_endpoints", 1),
    ]

    security_levels = (
        "Development",
        "Staging",
        "Production",
        "Critical Infrastructure",
    )
    blocked_users = {"migrated_user", "container_breach", "pipeline_compromise"}

    print("\n" + "=" * 60)
    print("СПИСОК РЕСУРСІВ СИСТЕМИ:")
    print("=" * 60)
    for res_name, lvl in resources:
        level_label = security_levels[lvl - 1]
        print(f"Ресурс: {res_name:<25} | Рівень: {level_label}")

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТИ ПЕРЕВІРКИ ДОСТУПУ:")
    print("=" * 60)
    for u_name in users:
        for r_name, _ in resources:
            allowed, reason = check_access(
                u_name, r_name, users, resources, blocked_users
            )
            verdict = "ALLOW" if allowed else f"DENY ({reason})"
            print(f"user={u_name:<16} resource={r_name:<23} -> {verdict}")


if __name__ == "__main__":
    run_task2()
