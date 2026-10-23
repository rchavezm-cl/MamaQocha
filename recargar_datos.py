"""
Script de utilidad para inicializar o recargar la base de datos de Mamá Qocha.
Aplica schema.sql y seed_demo.sql en la base de datos configurada (DATABASE_URL o .env).
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv(override=True)

def obtener_db_url() -> str:
    # Si se pasa como argumento de línea de comando: python recargar_datos.py "postgresql://..."
    if len(sys.argv) > 1 and sys.argv[1].startswith("postgres"):
        return sys.argv[1]
    
    url = os.getenv("DATABASE_URL")
    if not url:
        pg_host = os.getenv("PG_HOST", "localhost")
        pg_port = os.getenv("PG_PORT", "5432")
        pg_database = os.getenv("PG_DATABASE", "mama_qocha")
        pg_user = os.getenv("PG_USER", "postgres")
        pg_password = os.getenv("PG_PASSWORD", "")
        url = f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

def ejecutar_script_sql(conn, file_path: str, nombre: str):
    if not os.path.exists(file_path):
        print(f"[ERROR] No se encontro el archivo {file_path}")
        return False
    
    print(f"-> Ejecutando {nombre} ({file_path})...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Usar cursor raw de psycopg para permitir múltiples comandos/transacciones
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"   [OK] {nombre} ejecutado con exito.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"   [ERROR] Fallo al ejecutar {nombre}: {e}")
        return False
    finally:
        cursor.close()

def main():
    db_url = obtener_db_url()
    # Ocultar password en consola
    url_segura = db_url.split("@")[-1] if "@" in db_url else db_url
    print("=" * 60)
    print("  MAMA QOCHA - Inicializador / Recarga de Dataset")
    print(f"  Destino: ...@{url_segura}")
    print("=" * 60)

    try:
        engine = create_engine(db_url)
        raw_conn = engine.raw_connection()
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, "schema.sql")
    seed_path = os.path.join(base_dir, "seed_demo.sql")

    exito_schema = ejecutar_script_sql(raw_conn, schema_path, "1. Esquema de Tablas (schema.sql)")
    if exito_schema:
        ejecutar_script_sql(raw_conn, seed_path, "2. Dataset de Prueba (seed_demo.sql)")

    raw_conn.close()
    print("=" * 60)
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
