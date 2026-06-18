# Fix errore Render: Not Found

## Causa
La versione `focus360_ai_alpha_microservices_devsecops_render_fix.zip` avviava correttamente Gunicorn, ma l'entrypoint puntava all'API Gateway microservizi, che esponeva solo:

- `/health`
- `/api/<service>/<path>`

Aprendo l'URL principale Render (`/`) compariva quindi:

```text
Not Found
The requested URL was not found on the server.
```

## Correzione applicata
Sono state aggiunte le route:

- `/` homepage gateway
- `/docs` note operative
- handler `404` più chiaro
- proxy API più robusto con gestione errori `502 service_unreachable`

## Deploy Render consigliato

```text
Build Command:
pip install --upgrade pip && pip install -r requirements.txt

Start Command:
gunicorn app:app --bind 0.0.0.0:$PORT
```

## Nota importante
Questa è la versione **microservizi/API Gateway**. Se vuoi la dashboard grafica completa, fai deploy della cartella:

```text
legacy_alpha_monolith
```

oppure crea un frontend separato che consumi gli endpoint del gateway.
