import socket
import json
import sys

# ==============================================================================
# CONFIGURACIÓN DEL CLIENTE
# ==============================================================================
HOST = "localhost"
PORT = 5000
BUFFER_SIZE = 1024

def enviar_tarea(sock, peticion):
    """
    Envía la petición en formato JSON al servidor y espera la respuesta del worker.
    """
    try:
        # Codificar y enviar
        sock.sendall(json.dumps(peticion).encode("utf-8"))

        # Recibir respuesta del servidor
        respuesta_bytes = sock.recv(BUFFER_SIZE)
        if not respuesta_bytes:
            print("[AVISO] El servidor cerró la conexión.")
            return None

        # Parsear respuesta JSON
        respuesta = json.loads(respuesta_bytes.decode("utf-8"))
        return respuesta
    except Exception as e:
        print(f"[ERROR COMUNICACIÓN] Error al enviar/recibir datos: {e}")
        return None

def mostrar_menu():
    print("\n" + "-" * 50)
    print("      MENÚ DE TAREAS - CLIENTE DISTRIBUIDO")
    print("-" * 50)
    print("1. Contar palabras y caracteres de un texto")
    print("2. Calcular números primos hasta un límite")
    print("3. Simular almacenamiento de archivo (PostgreSQL + S3)")
    print("4. Salir (o escribe 'éxito')")
    print("-" * 50)

def iniciar_cliente():
    print("=" * 60)
    print("   CLIENTE TCP DISTRIBUIDO - ENVÍO DE TAREAS")
    print("   Materia: Programación sobre Redes - IFTS N° 29")
    print("   Alumno: Rodrigo Berger")
    print("=" * 60)
    print(f"Conectando al servidor en {HOST}:{PORT}...")

    # 1. Crear y conectar el socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        print(f"[ÉXITO] Conexión establecida con el servidor {HOST}:{PORT}.\n")
    except ConnectionRefusedError:
        print(f"\n[ERROR CONEXIÓN] No se pudo conectar con {HOST}:{PORT}.")
        print("[AYUDA] Asegúrate de haber iniciado primero 'servidor.py' en otra terminal.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR INESPERADO] Error al inicializar cliente: {e}")
        sys.exit(1)

    # 2. Bucle principal de interacción
    try:
        while True:
            mostrar_menu()
            opcion = input("Elige una opción (1-4) > ").strip().lower()

            if opcion in ["4", "éxito", "exito", "salir"]:
                print("\n[INFO] Desconexión solicitada. Finalizando sesión...")
                client_socket.sendall("éxito".encode("utf-8"))
                break

            elif opcion == "1":
                texto = input("\nIngresa el texto a procesar > ").strip()
                if not texto:
                    texto = "Este es un texto de prueba para el sistema distribuido con workers"
                    print(f"Usando texto por defecto: \"{texto}\"")

                peticion = {
                    "tipo": "contar_palabras",
                    "parametros": {"texto": texto}
                }
                resp = enviar_tarea(client_socket, peticion)
                if resp:
                    print(f"\n✔ Atendido por: {resp.get('worker')} (en {resp.get('tiempo_ms')} ms)")
                    print(f"  Resultado: {resp.get('resultado')}")

            elif opcion == "2":
                limite_str = input("\nIngresa el límite superior para buscar primos (ej: 500) > ").strip()
                try:
                    limite = int(limite_str) if limite_str else 200
                except ValueError:
                    limite = 200
                    print("Valor inválido. Usando 200.")

                peticion = {
                    "tipo": "calcular_primos",
                    "parametros": {"limite": limite}
                }
                resp = enviar_tarea(client_socket, peticion)
                if resp:
                    print(f"\n✔ Atendido por: {resp.get('worker')} (en {resp.get('tiempo_ms')} ms)")
                    print(f"  Resultado: {resp.get('resultado')}")

            elif opcion == "3":
                nombre = input("\nNombre del archivo (ej: datos.csv) > ").strip()
                if not nombre:
                    nombre = "reporte.txt"
                contenido = input("Contenido o descripción del archivo > ").strip()
                if not contenido:
                    contenido = "Datos simulados del tercer trabajo práctico."

                peticion = {
                    "tipo": "guardar_archivo",
                    "parametros": {"nombre": nombre, "contenido": contenido}
                }
                resp = enviar_tarea(client_socket, peticion)
                if resp:
                    print(f"\n✔ Atendido por: {resp.get('worker')} (en {resp.get('tiempo_ms')} ms)")
                    print(f"  Resultado: {resp.get('resultado')}")

            else:
                print("[!] Opción inválida. Ingresa un número del 1 al 4.")

    except KeyboardInterrupt:
        print("\n\n[INFO] Programa interrumpido por el usuario (Ctrl+C).")
    finally:
        client_socket.close()
        print("[INFO] Socket cliente cerrado correctamente.")

if __name__ == "__main__":
    iniciar_cliente()
