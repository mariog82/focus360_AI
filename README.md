# Focus360 AI Enterprise v9 - Moduli reali per piano

Versione rigenerata con logica applicativa reale per i piani Base, Pro ed Enterprise/PNRR.

## Novità v9

- Menu dinamici in base al piano dell'istituto.
- Route protette lato server con `@require_feature`.
- Pagina `/modules` che mostra moduli attivi e non inclusi.
- Dashboard Dirigente, Docente, Studente e Genitore adattate al piano.
- Base: solo QR, Focus Mode, CSV, dashboard e report CSV.
- Pro: aggiunge AI Analytics, Digital Wellness Score, Passport, gamification completa e interventi.
- Enterprise/PNRR: aggiunge Smart Locker, blockchain, API, registro elettronico e report ministeriali.
- API e registro restano disattivabili solo in Enterprise/PNRR.
- Smart Locker disponibile solo in Enterprise/PNRR e disattivabile dal SuperAdmin.

## Credenziali demo

- SuperAdmin: `superadmin@focus360.ai` / `admin123`
- Dirigente: `dirigente@demo.focus360.ai` / `dirigente123`
- Docente: `docente@demo.focus360.ai` / `docente123`
- Studente: `studente@demo.focus360.ai` / `studente123`
- Genitore: `genitore@demo.focus360.ai` / `genitore123`

## Test dei piani

1. Accedi come SuperAdmin.
2. Crea o modifica un istituto.
3. Cambia piano Base, Pro o Enterprise.
4. Accedi come Dirigente/Docente/Studente.
5. Verifica che il menu mostri solo i moduli del piano.
6. Apri `/modules` per vedere il riepilogo operativo.

## Deploy Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:app
```

Variabili consigliate:

```env
SECRET_KEY=chiave-lunga-sicura
DATABASE_URL=sqlite:///focus360_ai.db
PHONEBOX_API_KEY=demo-phonebox-key
```

Per produzione usare PostgreSQL Render.
