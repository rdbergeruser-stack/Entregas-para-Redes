import socket
import sys

# ==============================================================================
# CONFIGURACIÓN DEL CLIENTE
# ==============================================================================
# Parámetros para conectar al servidor
HOST = "localhost" # Dirección del servidor local
PORT = 5000        # Puerto del servidor especificado en la consigna

def iniciar_cliente():
    """
    Inicia la conexión con el servidor de sockets, envía múltiples mensajes
    en un bucle interactivo y muestra la respuesta del servidor para cada uno.
    Finaliza la sesión cuando el usuario escribe 'éxito' (o 'exito').
    """
    print("=" * 60)
    print("   CLIENTE DE CHAT TCP/IP")
    print("=" * 60)
    print(f"Conectando al servidor en {HOST}:{PORT}...")

    # 1. Configuración y creación del socket cliente
    try:
        # Socket TCP/IP IPv4
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Conexión al socket del servidor
        client_socket.connect((HOST, PORT))
        print(f"[ÉXITO] Conexión establecida con el servidor {HOST}:{PORT}.")
        print("-> Escribe tus mensajes a continuación.")
        print("-> Para salir del programa escribe: éxito\n")
        
    except ConnectionRefusedError:
        # Manejo de error si el servidor no está en ejecución
        print(f"\n[ERROR CONEXIÓN] No se pudo conectar con {HOST}:{PORT}.")
        print("[AYUDA] Asegúrate de haber iniciado primero 'servidor.py' en otra terminal.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR INESPERADO] Error al inicializar cliente: {e}")
        sys.exit(1)

    # 2. Bucle interactivo para enviar múltiples mensajes
    try:
        while True:
            # Captura de mensaje del usuario
            mensaje = input("Tú > ")
            
            # Ignorar entradas vacías
            if not mensaje.strip():
                continue

            # Enviar el mensaje codificado en bytes (UTF-8)
            client_socket.sendall(mensaje.encode("utf-8"))

            # Condición de salida: si el usuario escribe 'éxito' o 'exito'
            if mensaje.strip().lower() in ["éxito", "exito"]:
                print("\n[INFO] Desconexión solicitada por el usuario. Finalizando...")
                break

            # 3. Recibir la respuesta del servidor (buffer de 1024 bytes)
            respuesta = client_socket.recv(1024).decode("utf-8")
            
            if not respuesta:
                print("\n[AVISO] El servidor cerró la conexión.")
                break
                
            # Mostrar la respuesta del servidor
            print(f"Servidor > {respuesta}\n")

    except KeyboardInterrupt:
        print("\n\n[INFO] Programa interrumpido por el usuario (Ctrl+C).")
    except Exception as e:
        print(f"\n[ERROR COMUNICACIÓN] Ocurrió un error en la transmisión de datos: {e}")
    finally:
        # 4. Cierre seguro del socket
        client_socket.close()
        print("[INFO] Socket cliente cerrado correctamente.")

if __name__ == "__main__":
    iniciar_cliente()
