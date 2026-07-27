from migrators.families import migrate as migrate_families
from migrators.products import migrate as migrate_products


def mostrar_menu():
    print()
    print("=" * 50)
    print("AGORA DATA BRIDGE")
    print("=" * 50)
    print("1 - Migrar Familias")
    print("2 - Migrar Productos")
    print("0 - Salir")
    print()


def main():
    while True:

        mostrar_menu()

        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            migrate_families()

        elif opcion == "2":
            migrate_products()

        elif opcion == "0":
            print()
            print("Hasta pronto.")
            break

        else:
            print()
            print("Opcion no valida.")


if __name__ == "__main__":
    main()
