LINE = "=" * 70
SEPARATOR = "-" * 70


def title(text):
    print()
    print(LINE)
    print(text)
    print(LINE)


def section(text):
    print()
    print(SEPARATOR)
    print(text)
    print(SEPARATOR)


def info(label, value):
    print(f"{label:<20}: {value}")


def success(text):
    print(f"[OK] {text}")


def warning(text):
    print(f"[WARN] {text}")


def error(text):
    print(f"[ERROR] {text}")


def product(index, total, code, name):
    print()
    print(SEPARATOR)
    print(f"[{index}/{total}]")
    print(f"Codigo              : {code}")
    print(f"Nombre              : {name}")
    print(SEPARATOR)
