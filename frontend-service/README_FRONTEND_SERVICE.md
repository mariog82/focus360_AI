# Focus360 AI Frontend-Service

Questa cartella contiene il monolite `legacy_alpha_monolith` trasformato in **frontend-service** grafico per demo SaaS.

## Funzioni
- Login grafico Bootstrap.
- Dashboard esistenti SuperAdmin, Dirigente, Docente, Studente, Genitore.
- UI commerciale per demo con dirigenti scolastici.
- Collegamento al Gateway tramite `GATEWAY_URL`.
- Pagina `/system-status` per verificare `/health` e `/health/services` del Gateway.

## Variabili
```env
SECRET_KEY=change-me
DATABASE_URL=sqlite:///focus360_ai.db
GATEWAY_URL=http://gateway:8080
FRONTEND_MODE=frontend-service
```

## Locale con Docker Compose
```bash
docker compose up --build
```
Frontend: http://localhost:8090  
Gateway: http://localhost:8080

## Render
Crea un Web Service separato:
- Root Directory: `frontend-service`
- Environment: Docker
- Dockerfile Path: `Dockerfile`
- Variabile `GATEWAY_URL`: URL pubblico o privato del Gateway Render.
