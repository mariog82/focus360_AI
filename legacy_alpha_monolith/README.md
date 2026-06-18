# Focus360 AI Enterprise Alpha

Versione Alpha derivata dalla beta v12. In questa build sono implementati e riattivati i moduli Enterprise relativi a:

- **Smart Locker / Phone Box** (`/lockers`)
- **API integrazioni** (`/api-console`, `/api/v1/focus-summary`, `/api/analytics`, `/api/v1/device-event`, `/api/v1/phonebox/event`)
- **Registro elettronico** (`/registro`)
- **Multi-plesso** (`/plessi`)

## Credenziali demo

| Ruolo | Email | Password |
|---|---|---|
| SuperAdmin | `superadmin@focus360.ai` | `admin123` |
| Dirigente | `dirigente@demo.focus360.ai` | `dirigente123` |
| Docente | `docente@demo.focus360.ai` | `docente123` |
| Studente | `studente@demo.focus360.ai` | `studente123` |
| Genitore | `genitore@demo.focus360.ai` | `genitore123` |

## Moduli per piano

### Base
- QR docente
- Focus Mode studente
- dashboard base
- upload CSV
- report CSV
- gamification essenziale

### Pro
- tutto Base
- AI Analytics
- Digital Wellness Score
- Educational Passport
- ranking
- report famiglie
- piani di intervento

### Enterprise/PNRR Alpha
- tutto Pro
- multi-plesso
- blockchain badge
- report ministeriali
- Smart Locker / Phone Box
- API integrazioni
- registro elettronico prototipo
- supporto prioritario

## Smart Locker / Phone Box

Pagina: `/lockers`

Permette di:
- creare box/locker per classe;
- simulare deposito telefono;
- simulare ritiro telefono;
- mettere un box in manutenzione;
- ricevere eventi hardware tramite API.

Endpoint hardware:

```http
POST /api/v1/phonebox/event
```

Esempio JSON:

```json
{
  "api_key": "demo-phonebox-key",
  "box_code": "3AINF-BOX-01",
  "event": "deposit",
  "student_email": "studente@demo.focus360.ai"
}
```

Eventi supportati: `deposit`, `withdraw`, `heartbeat`, `maintenance`.

## API Alpha

Pagina: `/api-console`

Endpoint disponibili:

```http
GET /api/v1/focus-summary
GET /api/analytics
POST /api/v1/device-event
POST /api/v1/phonebox/event
```

## Registro elettronico Alpha

Pagina: `/registro`

Permette di configurare un connettore dimostrativo verso:
- Argo;
- ClasseViva/Spaggiari;
- Axios;
- Nuvola;
- altro endpoint/API.

Funzioni simulate:
- sincronizzazione studenti;
- sincronizzazione docenti;
- sincronizzazione lezioni/classi;
- invio report Focus.

In produzione servono accordi/API ufficiali del fornitore del registro elettronico e gestione sicura di token/OAuth.

## Deploy Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```

Variabili consigliate:

```bash
SECRET_KEY=chiave_lunga_sicura
DATABASE_URL=sqlite:///focus360_ai.db
PHONEBOX_API_KEY=demo-phonebox-key
```

Per produzione usare PostgreSQL Render.
