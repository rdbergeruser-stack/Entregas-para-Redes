import socket
import sqlite3
import threading
from datetime import datetime

# ==============================================================================
# CONFIGURACIÓN GENERAL DEL SERVIDOR
# ==============================================================================
# Definición del host y puerto según requerimientos de la consigna del TP
HOST = "localhost"        # Dirección IP local / loopback
PORT = 5000               # Puerto TCP especificado en el TP
DB_NAME = "chat_db.sqlite" # Nombre del archivo de base de datos SQLite

# ==============================================================================
# 1. FUNCIÓN: INICIALIZAR BASE DE DATOS
# ==============================================================================
def inicializar_db():
    """
    Crea la base de datos SQLite y la tabla 'mensajes' si no existen.
    Campos obligatorios: id, contenido, fecha_envio, ip_cliente.
    """
    try:
        # Configuración y conexión con SQLite
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Sentencia DDL para crear la tabla de persistencia de mensajes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contenido TEXT NOT NULL,
                fecha_envio TEXT NOT NULL,
                ip_cliente TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("[DB] Base de datos e inicialización de tablas completada con éxito.")
    except sqlite3.Error as e:
        print(f"[ERROR DB] Error al inicializar o acceder a la base de datos: {e}")
        raise SystemExit(1)

# ==============================================================================
# 2. FUNCIÓN: GUARDAR MENSAJE EN LA BASE DE DATOS
# ==============================================================================
def guardar_mensaje(contenido, ip_cliente, fecha_envio):
    """
    Inserta un mensaje recibido en la base de datos SQLite.
    Cada hilo abre y cierra su propia conexión a la BD para garantizar la seguridad
    en concurrencia (thread-safety en SQLite).
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Inserción parametrizada para evitar inyección SQL
        cursor.execute('''
            INSERT INTO mensajes (contenido, fecha_envio, ip_cliente)
            VALUES (?, ?, ?)
        ''', (contenido, fecha_envio, ip_cliente))
        
        conn.commit()
        conn.close()
        print(f"[DB REGISTRO] Mensaje guardado -> De: {ip_cliente} | Fecha: {fecha_envio}")
    except sqlite3.Error as e:
        print(f"[ERROR DB] No se pudo guardar el mensaje en la base de datos: {e}")

# ==============================================================================
# 3. FUNCIÓN: INICIALIZAR EL SOCKET DEL SERVIDOR
# ==============================================================================
def inicializar_socket(host=HOST, port=PORT):
    """
    Crea, configura y enlaza (bind) el socket TCP/IP del servidor.
    Maneja excepciones en caso de que el puerto se encuentre ocupado o inaccesible.
    """
    try:
        # Configuración del socket TCP/IP:
        # AF_INET: Familia de direcciones IPv4
        # SOCK_STREAM: Protocolo TCP orientado a conexión
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # SO_REUSEADDR permite liberar y reutilizar inmediatamente el puerto tras reiniciar
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Vinculación del socket a la dirección IP y puerto
        server_socket.bind((host, port))
        
        # Poner el socket en modo de escucha con una cola de conexiones pendientes
        server_socket.listen(5)
        print(f"[SERVIDOR] Servidor escuchando activamente en {host}:{port}...")
        return server_socket

    except OSError as e:
        # Manejo de error específico: Puerto ocupado (Address already in use)
        print(f"[ERROR RED] El puerto {port} se encuentra ocupado o bloqueado: {e}")
        raise SystemExit(1)
    except Exception as e:
        print(f"[ERROR INESPERADO] Error al inicializar el socket del servidor: {e}")
        raise SystemExit(1)

# ==============================================================================
# 4. FUNCIÓN: GESTIONAR CONEXIÓN Y RECIBIR MENSAJES (POR CLIENTE)
# ==============================================================================
def atender_cliente(conn, addr):
    """
    Maneja la comunicación bidireccional con un cliente conectado en un hilo independiente.
    Recibe mensajes, los persiste en BD y envía la confirmación con timestamp.
    """
    ip_cliente = addr[0]
    puerto_cliente = addr[1]
    print(f"[NUEVA CONEXIÓN] Conexión establecida desde {ip_cliente}:{puerto_cliente}")

    try:
        while True:
            # Recepción de datos del cliente (buffer de 1024 bytes)
            datos = conn.recv(1024)
            if not datos:
                # Si no llegan datos, el socket del cliente fue cerrado
                break
            
            contenido_mensaje = datos.decode("utf-8").strip()
            
            # Condición de salida / desconexión voluntaria
            if contenido_mensaje.lower() in ["éxito", "exito"]:
                print(f"[DESCONEXIÓN] El cliente {ip_cliente}:{puerto_cliente} solicitó desconexión.")
                break

            # Generar timestamp con fecha y hora actual
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Guardar el contenido en la base de datos SQLite
            guardar_mensaje(contenido_mensaje, ip_cliente, timestamp)
            
            # Formato de respuesta exigido por el TP: "Mensaje recibido: <timestamp>"
            respuesta = f"Mensaje recibido: {timestamp}"
            conn.sendall(respuesta.encode("utf-8"))

    except ConnectionResetError:
        print(f"[AVISO RED] El cliente {ip_cliente}:{puerto_cliente} cerró la conexión inesperadamente.")
    except Exception as e:
        print(f"[ERROR COMUNICACIÓN] Error al procesar datos del cliente {ip_cliente}: {e}")
    finally:
        # Cerrar el socket de conexión del cliente
        conn.close()
        print(f"[CONEXIÓN FINALIZADA] Sesión cerrada para {ip_cliente}:{puerto_cliente}")

# ==============================================================================
# 5. FUNCIÓN: INICIAR SERVIDOR (BUCLE PRINCIPAL)
# ==============================================================================
def iniciar_servidor():
    """
    Punto de entrada principal que coordina la inicialización de la BD,
    el socket y el bucle para aceptar múltiples conexiones entrantes.
    """
    print("=" * 60)
    print("   SERVIDOR DE CHAT CLIENTE-SERVIDOR CON PERSISTENCIA SQLITE")
    print("=" * 60)
    
    # 1. Inicializar la base de datos
    inicializar_db()
    
    # 2. Inicializar el socket del servidor
    server_socket = inicializar_socket()
    
    # 3. Bucle para aceptar conexiones concurrentes
    try:
        while True:
            # Bloquea hasta que un nuevo cliente solicita conexión
            conn, addr = server_socket.accept()
            
            # Creación de hilo (multithreading) para atender clientes concurrentes
            hilo_cliente = threading.Thread(target=atender_cliente, args=(conn, addr), daemon=True)
            hilo_cliente.start()
            
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Deteniendo servidor por señal del usuario (Ctrl+C)...")
    finally:
        server_socket.close()
        print("[SERVIDOR] Socket principal del servidor cerrado correctamente.")

# ==============================================================================
# BLOQUE DE EJECUCIÓN
# ==============================================================================
if __name__ == "__main__":
    iniciar_servidor()
