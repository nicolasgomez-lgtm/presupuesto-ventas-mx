# Presupuesto Ventas México — Julio 2026 · Foodology

Herramienta web para simular el presupuesto de ventas con palancas comerciales compartidas.

## ¿Qué hace?

- Muestra el presupuesto base de julio ponderado por día de la semana (DOW-weighted)
- Permite agregar, editar y borrar **palancas comerciales compartidas** (todos las ven)
- Desglose por ciudad, marca, plataforma, cocina y día a día
- Datos: snapshot de Redshift (3,614 combos cocina×marca×plataforma)

---

## Deploy en Render (10 minutos, gratis)

### Paso 1 — Sube el código a GitHub

1. Ve a https://github.com/new y crea un repo nuevo (ej. `presupuesto-ventas-mx`)
2. Sube todos los archivos de esta carpeta (botón **"uploading an existing file"** en GitHub)
3. Confirma el commit

### Paso 2 — Crea el servicio en Render

1. Ve a https://dashboard.render.com → **New → Web Service**
2. Conecta tu cuenta de GitHub y selecciona el repo que creaste
3. Render detecta automáticamente el `render.yaml`. Confirma:
   - **Runtime**: Python
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Haz clic en **Deploy**
5. En ~2 minutos tendrás una URL pública: `https://presupuesto-ventas-mx.onrender.com`

> **Nota sobre palancas**: Las palancas se guardan en el disco del servidor (`levers.json`).
> El `render.yaml` ya configura un disco persistente de 1GB para que no se pierdan al reiniciar.

---

## Actualizar los datos (nueva foto de Redshift)

Cuando quieras refrescar el presupuesto base:

1. Corre la query de `README_query.sql` en Redshift
2. Reemplaza `budget_data.json` con el nuevo resultado
3. Haz push al repo → Render re-deploya automáticamente

---

## Estructura de archivos

```
presupuesto-web/
├── main.py            ← Backend FastAPI (API de datos + palancas)
├── requirements.txt   ← Dependencias Python
├── render.yaml        ← Config de Render (deploy automático)
├── budget_data.json   ← Snapshot de datos Redshift (3,614 filas)
└── static/
    └── index.html     ← Toda la app frontend
```

---

## Botón "Actualizar datos" — Variables de entorno en Render

Para que el botón 🔄 funcione, configura estas variables en Render Dashboard → tu servicio → **Environment**:

| Variable           | Descripción                        |
|--------------------|------------------------------------|
| `REDSHIFT_HOST`    | Host de Redshift (sin puerto)      |
| `REDSHIFT_PORT`    | Puerto (default: `5439`)           |
| `REDSHIFT_DATABASE`| Nombre de la base de datos         |
| `REDSHIFT_USER`    | Usuario                            |
| `REDSHIFT_PASSWORD`| Contraseña                         |

**Comportamiento del botón:**
- En la **última semana de cada mes** aparece un banner amarillo sugiriendo actualizar
- El badge del header muestra la fecha del último update
- Al hacer clic, re-corre la query DOW-weighted sobre las últimas 3 semanas y actualiza todos los datos en pantalla
- Sin las variables de entorno configuradas, el botón muestra un error descriptivo
