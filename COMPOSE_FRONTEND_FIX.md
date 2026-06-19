# Focus360 AI - Fix Docker Compose Frontend + Microservizi

Questa versione corregge l'errore dei microservizi che uscivano con codice 3.

## Causa
Nel precedente `docker-compose.yml` i microservizi usavano Dockerfile interni, ad esempio:

```yaml
dockerfile: services/auth_service/Dockerfile
```

Con `context: .` quel Dockerfile copiava per errore l'`app.py` root/gateway invece dell'app del microservizio.

## Correzione
Ora il Compose usa i Dockerfile root dedicati:

```yaml
dockerfile: Dockerfile.auth_service
```

che avviano correttamente:

```bash
gunicorn -b 0.0.0.0:8000 services.auth_service.app:app
```

## Avvio pulito su Windows

```powershell
docker compose down -v
docker compose build --no-cache
docker compose up -d
docker compose ps
```

## URL

- Gateway: http://localhost:8080
- Gateway health: http://localhost:8080/health
- Stato microservizi: http://localhost:8080/health/services
- Frontend login: http://localhost:8090/login
- Frontend status: http://localhost:8090/system-status

## Test rapido

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_microservices.ps1
```

Se un container resta in errore:

```powershell
docker compose logs nome-servizio
```
