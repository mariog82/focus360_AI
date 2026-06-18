# Fix deploy Render - Focus360 AI Alpha Microservices

## Errore risolto

Render restituiva:

```text
ModuleNotFoundError: No module named 'app'
```

perché il progetto microservizi esponeva il gateway in:

```text
gateway/app.py
```

mentre Render stava avviando:

```text
gunicorn app:app
```

In questa versione è stato aggiunto un file root:

```text
app.py
```

che importa correttamente:

```python
from gateway.app import app
```

## Deploy consigliato su Render

Build Command:

```text
pip install --upgrade pip && pip install -r requirements.txt
```

Start Command:

```text
gunicorn app:app --bind 0.0.0.0:$PORT
```

## Nota architetturale

Su Render, questa configurazione pubblica il solo **API Gateway**.  
I singoli microservizi possono essere deployati come ulteriori Web Service oppure eseguiti tramite Docker Compose in ambiente VPS/Kubernetes.

Endpoint di controllo:

```text
/health
```
