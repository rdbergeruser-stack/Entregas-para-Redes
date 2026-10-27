# TP: Implementación de un Chat Básico Cliente-Servidor con Sockets y Base de Datos

**Materia:** Programación sobre redes - 3.° D
**Alumno:** Rodrigo Berger  
**Tecnologías:** Python 3, Sockets TCP/IP (`socket`), Concurrencia (`threading`), Base de Datos (`sqlite3`).

---

## 📌 Descripción del Proyecto
Este proyecto implementa una arquitectura **Cliente-Servidor** en Python para el intercambio de mensajes a través de sockets TCP y la persistencia automática de los mismos en una base de datos **SQLite**.

### Componentes Principales:
1. **`servidor.py`**:
   - Escucha peticiones TCP en `localhost:5000`.
   - Inicializa y gestiona la base de datos `chat_db.sqlite`.
   - Utiliza hilos (`threading.Thread`) para soportar múltiples conexiones simultáneas de clientes sin bloquear el socket principal.
   - Registra cada mensaje con: `id`, `contenido`, `fecha_envio` e `ip_cliente`.
   - Devuelve la confirmación al cliente: `"Mensaje recibido: <timestamp>"`.
   - Manejo robusto de errores (`puerto ocupado`, `fallas en BD`, `desconexión abrupta`).

2. **`cliente.py`**:
   - Se conecta al servidor en `localhost:5000`.
   - Permite enviar mensajes continuos en consola.
   - Muestra la respuesta y marca de tiempo devuelta por el servidor.
   - Finaliza la sesión cuando el usuario escribe **`éxito`** o `exito`.

---

## 🗄️ Estructura de la Base de Datos
Tabla: `mensajes`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Identificador único del mensaje |
| `contenido` | `TEXT` | Texto enviado por el cliente |
| `fecha_envio` | `TEXT` | Marca de tiempo (`YYYY-MM-DD HH:MM:SS`) |
| `ip_cliente` | `TEXT` | Dirección IP de origen del cliente |

---

## 🚀 Guía de Ejecución

### 1. Iniciar el Servidor
Abre una terminal y ejecuta:
```bash
python servidor.py
```
*Salida esperada:*
```text
============================================================
   SERVIDOR DE CHAT CLIENTE-SERVIDOR CON PERSISTENCIA SQLITE
============================================================
[DB] Base de datos e inicialización de tablas completada con éxito.
[SERVIDOR] Servidor escuchando activamente en localhost:5000...
```

### 2. Iniciar el Cliente
Abre **otra terminal** distinta y ejecuta:
```bash
python cliente.py
```
*Ejemplo de interacción:*
```text
============================================================
   CLIENTE DE CHAT TCP/IP
============================================================
Conectando al servidor en localhost:5000...
[ÉXITO] Conexión establecida con el servidor localhost:5000.
-> Escribe tus mensajes a continuación.
-> Para salir del programa escribe: éxito

Tú > Hola, este es un mensaje de prueba
Servidor > Mensaje recibido: 2026-04-14 18:30:12

Tú > Segundo mensaje para verificar la persistencia
Servidor > Mensaje recibido: 2026-04-14 18:30:18

Tú > éxito

[INFO] Desconexión solicitada por el usuario. Finalizando...
[INFO] Socket cliente cerrado correctamente.
```

---

## 🧪 Pruebas y Casos de Error Manejados
- **Puerto Ocupado (`OSError`):** Si el puerto `5000` está en uso, el servidor lo informa claramente sin crashear. Además, se configuró `SO_REUSEADDR` para liberar el puerto inmediatamente tras reiniciar.
- **Servidor Apagado (`ConnectionRefusedError`):** Si el cliente intenta conectarse antes de iniciar el servidor, muestra un mensaje amigable indicando que debe iniciar primero `servidor.py`.
- **Concurrencia Segura en SQLite:** Cada hilo abre y cierra su conexión a la BD, evitando problemas de concurrencia y bloqueos entre clientes simultáneos.
