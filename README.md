# Focus360 AI Enterprise v6

Piattaforma Flask multi-istituto per benessere digitale, modalità Focus, gamification, Digital Wellness Score, Educational Passport, gestione licenze e moduli.

## Credenziali demo

- SuperAdmin: `superadmin@focus360.ai` / `admin123`
- Dirigente: `dirigente@demo.focus360.ai` / `dirigente123`
- Docente: `docente@demo.focus360.ai` / `docente123`
- Studente: `studente@demo.focus360.ai` / `studente123`
- Genitore: `genitore@demo.focus360.ai` / `genitore123`

Nel primo accesso gli utenti creati via CSV devono cambiare password. Nel prototipo demo gli utenti predefiniti possono essere rigenerati dal SuperAdmin.

## Novità v6

- Dirigente: gestione/edit utenti creati, reset password temporanea, disattivazione utenti.
- SuperAdmin: modifica completa dell’istituto, campi obbligatori, scadenza licenza, pagamento, piano, moduli, smart locker ON/OFF.
- SuperAdmin: avviso scadenza abbonamento con testo email/manuale e invio SMTP se configurato.
- Password: tutti i campi password hanno pulsante Mostra/Nascondi.
- Correzione Passport per dirigente, docente, studente e genitore.
- Correzione associazione genitore-studente tramite `parent_student_id`.
- Upload CSV docenti/studenti abilitato nei piani Base, Pro ed Enterprise/PNRR.
- Differenze piani visibili nella pagina `/plans`.

## Differenze pacchetti

### Base
- QR docente
- app Focus studente
- dashboard essenziale
- upload CSV docenti/studenti
- report CSV

### Pro
- tutto Base
- AI Analytics
- gamification
- ranking classi/scuole
- Digital Wellness Score
- Educational Passport
- report famiglie

### Enterprise/PNRR
- tutto Pro
- Smart Locker / Phone Box
- blockchain badge
- API hardware/mobile
- report ministeriali
- integrazione registro elettronico
- moduli gestibili/disattivabili dal SuperAdmin

## CSV Docenti

Separatore `;`:

```csv
cognome;nome;disciplina;mail;telefono;classe
Rossi;Mario;Informatica;mario.rossi@scuola.it;3331112222;4A
```

## CSV Studenti

```csv
cognome;nome;data di nascita;email;telefono;classe;email_genitore
Bianchi;Luca;2009-04-15;luca.bianchi@studenti.it;3334445555;4A;genitore.bianchi@email.it
```

Il sistema genera username=email e password temporanea casuale. Le credenziali possono essere esportate da Dirigente o SuperAdmin.

## Avvisi scadenza licenza

Il SuperAdmin vede gli istituti in scadenza entro 30 giorni e può usare il pulsante `Invia avviso scadenza`.

Se si configurano variabili SMTP, l’app prova l’invio automatico:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_TLS=1
SMTP_USER=utente
SMTP_PASSWORD=password
SMTP_FROM=noreply@focus360.ai
```

Se SMTP non è configurato, viene mostrato un link `mailto:` e il testo già pronto.

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
SECRET_KEY=chiave_lunga_sicura
DATABASE_URL=sqlite:///focus360_ai.db
PHONEBOX_API_KEY=demo-phonebox-key
```

Per produzione reale usare PostgreSQL Render al posto di SQLite.
