# Pasos para instalar el proyecto:

1 - Descarga el proyecto o clona el repositorio
2 - crea un entorno virtual con venv 

```bash
python -m venv .venv
.venv\Scripts\activate
# .venv/bin/activate # Linux
```

3 - instala las dependencias necesarias
```bash
pip install -r requirements.txt
```

4 - crea un archivo .env con tu GEMINI_API_KEY
```bash
echo "GEMINI_API_KEY='tu_api_key_aquí'" > .env
```

5 - ejecuta el proyecto y revisa el resultado

---
> Desarrollado por: Nelson Guerrero, V-32067861