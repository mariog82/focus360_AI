# Focus360 AI Enterprise v7

Piattaforma Flask multi-istituto per benessere digitale, modalità Focus, gamification, Digital Wellness Score, Educational Passport, gestione licenze, moduli e piani commerciali.

## Credenziali demo

- SuperAdmin: `superadmin@focus360.ai` / `admin123`
- Dirigente: `dirigente@demo.focus360.ai` / `dirigente123`
- Docente: `docente@demo.focus360.ai` / `docente123`
- Studente: `studente@demo.focus360.ai` / `studente123`
- Genitore: `genitore@demo.focus360.ai` / `genitore123`

## Novità v7

- Campi obbligatori evidenziati con bordo rosso se non compilati.
- Messaggio chiaro: “Completa tutti i campi obbligatori evidenziati in rosso”.
- API e integrazione registro elettronico disponibili e disattivabili solo nel piano Enterprise/PNRR.
- Smart Locker/Phone Box disponibile solo nel piano Enterprise/PNRR e disattivabile dal SuperAdmin.
- Redistribuzione dei moduli nei pacchetti Base, Pro, Enterprise/PNRR.
- Prezzi ricalcolati in modo più sostenibile per le scuole.
- Pagina `/plans` aggiornata con tabella comparativa.

## Prezzi consigliati

### Pacchetto Base — € 1.200/anno + IVA

Per scuole che vogliono iniziare senza hardware.

Include:
- QR docente;
- Focus Mode studente;
- dashboard docente/dirigente;
- upload CSV docenti/studenti/genitori;
- credenziali temporanee;
- report CSV base;
- gamification essenziale.

### Pacchetto Pro — € 2.900/anno + IVA

È il piano consigliato e più vendibile.

Include tutto il Base, più:
- AI Analytics;
- Digital Wellness Score;
- Educational Passport PDF;
- gamification completa;
- ranking classi;
- report famiglie;
- piani di intervento.

### Enterprise/PNRR — € 6.900/anno + IVA

Per reti di scuole, scuole tecniche e progetti PNRR.

Include tutto il Pro, più:
- Smart Locker / Phone Box;
- blockchain badge;
- API;
- integrazione registro elettronico;
- report ministeriali;
- multi-plesso;
- supporto prioritario.

Hardware, installazione, formazione avanzata e integrazioni con registro elettronico vanno quotati separatamente.

## Logica moduli

- Base e Pro non possono avere `api` e `registro`.
- Solo Enterprise/PNRR può usare e disabilitare `api` e `registro`.
- Smart Locker è forzato OFF nei piani Base e Pro.
- Se il SuperAdmin passa un istituto da Enterprise a Pro/Base, API, registro e locker vengono automaticamente esclusi.

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

