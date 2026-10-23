import os
import db

def test_neon():
    print("Testing Neon Lakebase Postgres connectivity...")
    print(f"DATABASE_URL host: {db.DATABASE_URL.split('@')[-1] if '@' in db.DATABASE_URL else 'local'}")
    
    # 1. Load locales
    locales = db.load_locales()
    print(f"[PASS] Loaded {len(locales)} locales from Neon.")
    assert len(locales) >= 5, "Expected at least 5 locales"

    # 2. Load proveedores
    proveedores = db.load_proveedores()
    print(f"[PASS] Loaded {len(proveedores)} proveedores from Neon.")
    assert len(proveedores) >= 4, "Expected at least 4 proveedores"

    # 3. Load productos
    productos = db.load_productos()
    print(f"[PASS] Loaded {len(productos)} productos from Neon.")
    assert len(productos) >= 7, "Expected at least 7 productos"

    # 4. Load metricas
    metricas = db.load_resumen_metricas()
    print(f"[PASS] Resumen metricas: {metricas}")

    # 5. Load alertas
    alertas = db.load_inventario_alertas()
    print(f"[PASS] Inventario alertas: {len(alertas)} registros.")

    print("\nALL NEON POSTGRES END-TO-END TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_neon()
