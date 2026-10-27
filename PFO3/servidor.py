import socket
import threading
import queue
import json
import time
from datetime import datetime

# ==============================================================================
# CONFIGURACIÓN DEL SERVIDOR
# ==============================================================================
HOST = "localhost"
PORT = 5000
NUM_WORKERS = 3       # Cantidad de hilos en el pool de workers
BUFFER_SIZE = 1024

# Cola sincronizada donde se encolan las tareas para los workers
cola_tareas = queue.Queue()

# ==============================================================================
# 1. FUNCIONES DE PROCESAMIENTO (TAREAS DE LOS WORKERS)
# ==============================================================================
def procesar_tarea(tipo, parametros):
    """
    Ejecuta el trabajo asignado al worker según el tipo de tarea recibida.
    """
    if tipo == "contar_palabras":
        texto = parametros.get("texto", "")
        palabras = texto.split()
        return {
            "total_caracteres": len(texto),
            "total_palabras": len(palabras)
        }

    elif tipo == "calcular_primos":
        limite = int(parametros.get("limite", 100))
        # Búsqueda de primos simple
        primos = []
        for n in range(2, limite + 1):
            es_primo = True
            for i in range(2, int(n**0.5) + 1):
                if n % i == 0:
                    es_primo = False
                    break
            if es_primo:
                primos.append(n)
        return {
            "limite": limite,
            "cantidad_primos": len(primos),
            "ultimos_primos": primos[-5:] if len(primos) >= 5 else primos
        }

    elif tipo == "guardar_archivo":
        # Simula la persistencia distribuida (PostgreSQL para metadatos y S3 para el archivo)
        nombre = parametros.get("nombre", "archivo.txt")
        contenido = parametros.get("contenido", "")
        time.sleep(0.5)  # Simula latencia de almacenamiento distribuido
        return {
            "mensaje": f"Archivo '{nombre}' guardado correctamente",
            "postgres_registro": f"ID-{int(time.time())}",
            "s3_path": f"s3://bucket-distribuido/{nombre}",
            "bytes": len(contenido)
        }

    else:
        return {"error": f"Tipo de tarea '{tipo}' no reconocido."}

# ==============================================================================
# 2. HILO TRABAJADOR (WORKER THREAD)
# ==============================================================================
def worker_loop(id_worker):
    """
    Bucle de ejecución de cada hilo trabajador del pool.
    Espera una tarea en la cola, la procesa y notifica cuando terminó.
    """
    print(f"[WORKER {id_worker}] Iniciado y listo para recibir tareas.")
    while True:
        try:
            # Bloquea hasta que haya una tarea disponible en la cola
            tipo, parametros, evento_fin, contenedor_resultado = cola_tareas.get()

            print(f"[WORKER {id_worker}] Tomando tarea: '{tipo}'...")
            inicio = time.time()

            # Procesamos la tarea
            resultado = procesar_tarea(tipo, parametros)
            duracion = round((time.time() - inicio) * 1000, 2)

            # Guardamos el resultado en el diccionario compartido
            contenedor_resultado["status"] = "OK"
            contenedor_resultado["worker"] = f"Worker-{id_worker}"
            contenedor_resultado["tipo"] = tipo
            contenedor_resultado["resultado"] = resultado
            contenedor_resultado["tiempo_ms"] = duracion

            print(f"[WORKER {id_worker}] Tarea '{tipo}' completada en {duracion} ms.")

            # Marcamos la tarea como finalizada en la cola y avisamos al socket
            cola_tareas.task_done()
            evento_fin.set()

        except Exception as e:
            print(f"[ERROR WORKER {id_worker}] Ocurrió un error al procesar la tarea: {e}")

# ==============================================================================
# 3. ATENCIÓN DE CLIENTES POR SOCKET
# ==============================================================================
def atender_cliente(conn, addr):
    """
    Maneja la conexión por socket con el cliente.
    Recibe la tarea en JSON, la manda a la cola de workers y devuelve el resultado.
    """
    ip_cliente = addr[0]
    puerto_cliente = addr[1]
    print(f"[NUEVA CONEXIÓN] Cliente conectado desde {ip_cliente}:{puerto_cliente}")

    try:
        while True:
            datos = conn.recv(BUFFER_SIZE)
            if not datos:
                break

            mensaje = datos.decode("utf-8").strip()

            # Condición de salida
            if mensaje.lower() in ["éxito", "exito", "salir"]:
                print(f"[DESCONEXIÓN] El cliente {ip_cliente}:{puerto_cliente} cerró la sesión.")
                break

            # Intentar parsear el JSON de la tarea enviada por el cliente
            try:
                peticion = json.loads(mensaje)
                tipo = peticion.get("tipo", "desconocido")
                parametros = peticion.get("parametros", {})

                # Creamos un evento para que el hilo de conexión espere a que el worker termine
                evento_fin = threading.Event()
                contenedor_resultado = {}

                # Encolamos la tarea para que la tome cualquier worker libre del pool
                cola_tareas.put((tipo, parametros, evento_fin, contenedor_resultado))

                # Esperamos a que el worker finalice
                evento_fin.wait(timeout=10.0)

                # Enviamos el resultado al cliente
                respuesta = json.dumps(contenedor_resultado)
                conn.sendall(respuesta.encode("utf-8"))

            except json.JSONDecodeError:
                error_msg = json.dumps({"status": "ERROR", "mensaje": "Formato JSON inválido"})
                conn.sendall(error_msg.encode("utf-8"))

    except ConnectionResetError:
        print(f"[AVISO RED] El cliente {ip_cliente}:{puerto_cliente} cerró la conexión abruptamente.")
    except Exception as e:
        print(f"[ERROR COMUNICACIÓN] Error con cliente {ip_cliente}: {e}")
    finally:
        conn.close()
        print(f"[CONEXIÓN FINALIZADA] Socket cerrado para {ip_cliente}:{puerto_cliente}")

# ==============================================================================
# 4. INICIAR SERVIDOR (BUCLE PRINCIPAL)
# ==============================================================================
def iniciar_servidor():
    print("=" * 60)
    print("   SERVIDOR DISTRIBUIDO CON POOL DE WORKERS")
    print("   Materia: Programación sobre Redes - IFTS N° 29")
    print("   Alumno: Rodrigo Berger")
    print("=" * 60)

    # 1. Iniciar el Pool de Workers
    print(f"[SISTEMA] Creando pool de {NUM_WORKERS} workers...")
    for i in range(1, NUM_WORKERS + 1):
        t = threading.Thread(target=worker_loop, args=(i,), daemon=True)
        t.start()

    # 2. Configurar el socket del servidor
    try:
        servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor_socket.bind((HOST, PORT))
        servidor_socket.listen(5)
        print(f"[SERVIDOR] Escuchando conexiones en {HOST}:{PORT}...")
    except OSError as e:
        print(f"[ERROR RED] No se pudo abrir el puerto {PORT}: {e}")
        return

    # 3. Aceptar clientes concurrentes
    try:
        while True:
            conn, addr = servidor_socket.accept()
            # Cada conexión de cliente se maneja en un hilo independiente
            hilo_cliente = threading.Thread(target=atender_cliente, args=(conn, addr), daemon=True)
            hilo_cliente.start()
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Deteniendo servidor (Ctrl+C)...")
    finally:
        servidor_socket.close()
        print("[SERVIDOR] Servidor detenido correctamente.")

if __name__ == "__main__":
    iniciar_servidor()
