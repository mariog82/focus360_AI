# Focus360 AI - Compose Fix v3

Questa versione corregge l'avvio locale Docker Compose:

- ogni microservizio usa un database SQLite separato per evitare lock concorrenti;
- l'inizializzazione DB è tollerante agli errori temporanei;
- `depends_on` non blocca più l'avvio dell'intero stack in caso di healthcheck lento;
- i servizi hanno `restart: unless-stopped`;
- aggiunto script Windows `scripts/check_local.ps1`.

## Avvio pulito

```powershell
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

## Verifica

```powershell
docker compose ps
powershell -ExecutionPolicy Bypass -File .\scripts\check_local.ps1
```

## URL

- Gateway: http://localhost:8080
- Health Gateway: http://localhost:8080/health
- Health microservizi: http://localhost:8080/health/services
- Frontend/Login: http://localhost:8090/login

## Se un servizio non parte

```powershell
docker compose logs compliance-service
docker compose logs auth-service
```
