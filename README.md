# Introduction 



# Login controller

---

## **Endpoints del Usuario**

### **1. Registro de Usuario**
- **Descripción:** Permite registrar un nuevo usuario.
- **Método:** `POST`
- **URL:** `/register`
- **Cuerpo de la Solicitud (JSON):**
```json
{
    "name": "John",
    "lastname": "Doe",
    "email": "johndoe@example.com",
    "password": "securepassword123"
}
```
- **Respuestas:**
  - **201 Created:**
    ```json
    {
        "message": "User created successfully"
    }
    ```
  - **400 Bad Request:** Usuario ya registrado o falta algún dato.

### **2. Inicio de Sesión**
- **Descripción:** Permite a un usuario autenticarse y obtener un token JWT.
- **Método:** `POST`
- **URL:** `/login`
- **Cuerpo de la Solicitud (JSON):**
```json
{
    "email": "johndoe@example.com",
    "password": "securepassword123"
}
```
- **Respuestas:**
  - **200 OK:**
    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
  - **401 Unauthorized:** Credenciales incorrectas.

### **3. Obtener Detalles del Usuario**
- **Descripción:** Devuelve los detalles del usuario autenticado.
- **Método:** `GET`
- **URL:** `/me`
- **Encabezados de Autorización:**
  - Clave: `Authorization`
  - Valor: `Bearer <TOKEN>`
- **Respuestas:**
  - **200 OK:**
    ```json
    {
        "id": 1,
        "name": "John",
        "lastname": "Doe",
        "email": "johndoe@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }
    ```
  - **401 Unauthorized:** Token faltante o inválido.

---

## **Probar los Endpoints en Postman**

### **1. Configurar Postman**
- Abre Postman y crea una nueva colección para organizar tus solicitudes.

### **2. Probar el Registro de Usuario**
1. Crea una nueva solicitud en Postman.
2. Selecciona el método `POST`.
3. Ingresa la URL de tu servidor, por ejemplo: `http://localhost:5000/register`.
4. En la pestaña **Body**, selecciona la opción **raw**, y elige el tipo `JSON`.
5. Copia el cuerpo de la solicitud proporcionado en el endpoint.
6. Envía la solicitud y verifica la respuesta.

### **3. Probar el Inicio de Sesión**
1. Crea una nueva solicitud en Postman.
2. Selecciona el método `POST`.
3. Ingresa la URL de tu servidor: `http://localhost:5000/login`.
4. En la pestaña **Body**, selecciona la opción **raw**, y elige el tipo `JSON`.
5. Copia el cuerpo de la solicitud proporcionado en el endpoint.
6. Envía la solicitud y copia el token recibido.

### **4. Probar Obtener Detalles del Usuario**
1. Crea una nueva solicitud en Postman.
2. Selecciona el método `GET`.
3. Ingresa la URL de tu servidor: `http://localhost:5000/me`.
4. Ve a la pestaña **Headers** y agrega un encabezado:
   - Clave: `Authorization`
   - Valor: `Bearer <TOKEN>` (reemplaza `<TOKEN>` con el token recibido del endpoint de login).
5. Envía la solicitud y verifica la respuesta.

---

### **Notas:**
1. Asegúrate de que el servidor esté corriendo antes de realizar las pruebas.
2. Usa una base de datos limpia al comenzar para evitar errores con usuarios duplicados.
3. Configura las variables de entorno en Postman para manejar fácilmente la URL base y el token JWT:
   - Crea una variable `BASE_URL` con el valor de tu servidor (e.g., `http://localhost:5000`).
   - Usa `{{BASE_URL}}/register` en lugar de escribir la URL completa.
   - Guarda el token JWT como variable `TOKEN` después de obtenerlo en el login.