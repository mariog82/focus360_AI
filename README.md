# Focus360 AI Enterprise v12

Versione derivata dalla v11 con correzioni richieste:

- Pulsante **Gestione multi-plesso** distanziato dai pulsanti principali nella dashboard Dirigente.
- Nuova pagina **Associa utenti** per collegare docenti, studenti e genitori a un plesso.
- Nel form di modifica utente è possibile assegnare/modificare il plesso.
- Nell'upload CSV docenti/studenti è possibile scegliere un plesso predefinito.
- Supportata la colonna CSV `plesso`, `codice_plesso` o `sede` per assegnazione automatica al plesso.
- Nella dashboard **Moduli del piano** e nella pagina `/modules` non vengono più mostrate le label dei moduli disabilitati dal SuperAdmin.
- I moduli `lockers`, `api` e `registro` restano disattivati.
- `multi_plesso` resta disponibile solo in Enterprise/PNRR.

## CSV multi-plesso

Esempio docenti:

```csv
cognome;nome;disciplina;email;telefono;classe;codice_plesso
Rossi;Mario;Informatica;mario.rossi@scuola.it;3331112222;4A;CENTRALE
```

Esempio studenti:

```csv
cognome;nome;data di nascita;email;telefono;classe;email_genitore;codice_plesso
Bianchi;Luca;2009-04-15;luca.bianchi@studenti.it;3334445555;4A;genitore@email.it;SUCCURSALE
```

## Credenziali demo

- SuperAdmin: `superadmin@focus360.ai` / `admin123`
- Dirigente: `dirigente@demo.focus360.ai` / `dirigente123`
- Docente: `docente@demo.focus360.ai` / `docente123`
- Studente: `studente@demo.focus360.ai` / `studente123`
- Genitore: `genitore@demo.focus360.ai` / `genitore123`
