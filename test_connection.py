from db import source_connection, agora_connection

print("=" * 50)
print("AGORA DATA BRIDGE")
print("=" * 50)

print("Conectando con MARTINEZ...")
src = source_connection()
print("OK")

print("Conectando con AGORA...")
dst = agora_connection()
print("OK")

src.close()
dst.close()

print()
print("Todas las conexiones funcionan correctamente.")
