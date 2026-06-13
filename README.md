# Focus360 AI

Webapp Flask multi-istituto per ridurre l'uso improprio dello smartphone a lezione attraverso gamification, benessere digitale, analytics AI e certificazioni educative blockchain-like.

## Funzioni principali

- Multi-tenant: SuperAdmin aziendale, Dirigente, Docente, Studente, Genitore.
- Piani commerciali: Base, Pro, Enterprise/PNRR.
- Upload CSV docenti e studenti.
- Generazione automatica credenziali.
- QR temporaneo docente per attivare la sessione Focus.
- Registro digitale: presenti, minuti focus, violazioni, punti, token.
- Gamification: FocusToken, badge, certificato cittadinanza digitale.
- Blockchain educativa simulata: hash immutabili per sessioni e badge NFT non speculativi.
- AI Analytics prototipo: indice di attenzione, risk score distrazione, ranking classi, ore recuperate.
- Check-in benessere digitale studente.
- Smart locker / phone box / NFC badge registry.
- Dashboard genitore.
- Report CSV e API `/api/v1/focus-summary`.

## Credenziali demo

Dopo `flask init-db`:

- SuperAdmin: `superadmin@focus360.ai`
- Password: `admin123`

## Avvio locale

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```

Aprire: `http://127.0.0.1:5000`

## CSV docenti

Separatore `;`:

```csv
cognome;nome;disciplina;mail;telefono;classe
Rossi;Mario;Informatica;m.rossi@scuola.it;3331111111;3A
```

## CSV studenti

```csv
cognome;nome;data di nascita;email;telefono;classe
Bianchi;Luca;2010-04-12;luca.bianchi@studenti.it;3332222222;3A
```

## Deploy su Render

1. Caricare il progetto su GitHub.
2. Creare un nuovo Web Service su Render collegato al repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Aggiungere variabili ambiente:
   - `SECRET_KEY`
   - `DATABASE_URL` se si usa PostgreSQL Render
6. Dopo il primo deploy, aprire una shell Render ed eseguire:
   - `flask --app app init-db`
7. Accedere con SuperAdmin e creare il primo istituto.

## Nota tecnica mobile

Il blocco effettivo di app/social su Android e iOS richiede una componente nativa, MDM scolastico o integrazione con strumenti di gestione dispositivo. La webapp simula la sessione e conserva la struttura dati pronta per integrazioni con:

- Android Digital Wellbeing / Device Policy Controller
- iOS Focus / Screen Time / MDM
- firewall e captive portal WiFi scolastico
- VLAN didattiche
- smart locker, NFC badge, smartwatch

