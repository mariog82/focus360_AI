# Focus360 AI

**Focus360 AI** è una webapp Flask multi-istituto per scuola secondaria pensata per migliorare concentrazione, benessere digitale e uso consapevole dello smartphone a lezione.

L'app non nasce come strumento punitivo, ma come piattaforma educativa: QR temporaneo del docente, registro focus, gamification, FocusToken, badge digitali, report per PTOF/Educazione civica/PCTO, dashboard per dirigente/docenti/studenti/genitori e funzioni commerciali per licenze annuali.

## Funzioni principali

- Multi-tenant: SuperAdmin, Dirigente, Docente, Studente, Genitore.
- Creazione istituti e licenze: Base, Pro, Enterprise/PNRR.
- Gestione fatturazione e pagamenti.
- Upload CSV docenti e studenti.
- Creazione automatica credenziali studenti/genitori.
- Avvio lezione con QR Code temporaneo.
- Registro digitale del focus.
- Punteggi, FocusToken e badge NFT educativi simulati.
- Blockchain interna prototipo con hash concatenati.
- AI Risk Score e Indice di attenzione.
- Check-in benessere digitale.
- Smart locker / phone box / NFC badge.
- Consensi informativi.
- Piani educativi di intervento.
- Report ministeriale stampabile e report CSV.
- API prototipo per app mobile / device-event.

## Credenziali demo

- Email: `superadmin@focus360.ai`
- Password: `admin123`

## Avvio locale

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Aprire: `http://127.0.0.1:5000`

## CSV docenti

Separatore `;`:

```csv
cognome;nome;disciplina;mail;telefono;classe
Rossi;Mario;Informatica;mario.rossi@scuola.it;3331112222;3A
```

## CSV studenti

Separatore `;`:

```csv
cognome;nome;data di nascita;email;telefono;classe
Bianchi;Luca;2010-05-12;luca.bianchi@studenti.it;3332221111;3A
```

## Deploy su Render

### 1. Crea un repository GitHub

Carica nella root del repository questi file:

- `app.py`
- `requirements.txt`
- `render.yaml`
- cartella `templates`
- cartella `examples`

### 2. Crea il Web Service

Su Render:

1. New +
2. Web Service
3. Build and deploy from a Git repository
4. seleziona il repository GitHub

### 3. Impostazioni Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```

### 4. Variabili d'ambiente

```text
SECRET_KEY=crea_una_chiave_lunga_e_sicura
DATABASE_URL=sqlite:///focus360_ai.db
```

Per produzione reale usare PostgreSQL Render:

1. New + → PostgreSQL
2. Copiare l'Internal Database URL
3. Inserirlo come `DATABASE_URL` nel Web Service

### 5. Nota importante su Render

SQLite va bene solo per test e demo. Per un prodotto commerciale utilizzare PostgreSQL, perché il filesystem dei servizi Render può essere effimero in base al piano e alla configurazione.

## Stack consigliato

- Frontend: Bootstrap 5, Chart.js, DataTables
- Backend: Flask, SQLAlchemy
- Database: SQLite demo, PostgreSQL produzione
- AI: pandas, numpy, scikit-learn
- Blockchain: prototipo hash-chain; in produzione Polygon o rete permissioned
- Mobile: app Android/iOS per Digital Wellbeing, Focus Mode, Screen Time e API device-event

## Nota privacy

Il prototipo non blocca realmente app Android/iOS dal browser. Il blocco notifiche/social richiede app mobile nativa, autorizzazioni esplicite, informativa privacy, consenso e configurazione MDM o integrazioni di sistema.
