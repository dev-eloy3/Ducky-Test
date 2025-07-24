# 🦆 Ducky Test – Plataforma de Evaluación de Conocimientos

## 📋 Descripción del módulo

**Ducky Test** es una aplicación web desarrollada con **Django** que permite gestionar y realizar tests por niveles (**básico, medio y avanzado**) para evaluar conocimientos, especialmente en programación.

Está diseñada para centros formativos, docentes y alumnos, facilitando la creación de tests, registro de usuarios y seguimiento de resultados.

---

## ⚙️ Manual de instalación

1. **Clona el repositorio o copia el proyecto**:

```bash
git clone https://github.com/dev-eloy3/Ducky-Test.git
cd ducky-main
```

2. **Crea un entorno virtual:**:
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

```

3. **Instala las dependencias:**
```bash
pip install -r requirements.txt

```

4. **Configura las variables de entorno en un archivo .env o .env.example:**
```bash
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

```

5. **Aplica las migraciones y crea un superusuario:**
```bash
python manage.py migrate
python manage.py createsuperuser

```
6. **Crear los grupos de:**
```bash
alumnos
Teachers
```
7. **(Opcional) Carga los tests predefinidos:**
```bash
python manage.py loaddata tests/python_basico_test.json

```
8. **Inicia el servidor:**
```bash
python manage.py runserver
```

## 🧪 Tecnologías usadas
- **Python**: 3.13
- **Django**: 5.2.4
- **Base de datos**: SQLite3 (por defecto)
- **Frontend**:
  - Bootstrap (integrado con crispy-forms)
  - HTML, CSS, JavaScript
- **Análisis de datos**: Pandas

## 👥 Roles del sistema

- **Administrador**: acceso completo a todos los módulos y usuarios.
- **Profesor**: puede visualizar tests y resultados de sus alumnos.
- **Alumno**: puede realizar tests asignados y consultar sus resultados.

## 👨‍🏫 Manual de usuario básico

### 🔐 Acceso

Visita: http://127.0.0.1:8000/

Regístrate o inicia sesión según tu rol (admin, profesor, alumno).

### ✅ Realizar un test (Alumno)

- Ve al menú de tests.
- Selecciona el nivel: básico, medio o avanzado.
- Responde todas las preguntas del test.
- Al finalizar, se mostrará tu resultado y retroalimentación.

### 📊 Visualizar resultados (Profesor/Admin)

- Accede a la sección “Resultados” desde el panel.
- Filtra por nivel, usuario o fecha.
- Consulta qué preguntas son más falladas para análisis pedagógico.
