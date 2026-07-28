from audits.common import run_audit


def audit_products():
    run_audit(
        "audit_products.sql",
        "AUDITORÍA DE PRODUCTOS"
    )


if __name__ == "__main__":
    audit_products()
