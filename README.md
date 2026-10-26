# Misure Schermi Smartphone

Sito di una sola pagina con larghezza e altezza dello schermo, misure della scocca e codici modello degli smartphone annunciati dal 2020. I modelli con le stesse misure sono raggruppati, così da trovare subito i telefoni compatibili (pellicole, cover, stampe).

## Come funziona

- `docs/index.html` è il sito vero e proprio, pubblicato con GitHub Pages.
- Il giorno 1 di ogni mese GitHub scarica il dataset aggiornato, ricalcola le misure e sostituisce la pagina. Non serve fare nulla.
- I dati vengono da [bytecharts/device_specs_gsmarena](https://github.com/bytecharts/device_specs_gsmarena) (specifiche GSMArena). Se la fonte non si aggiorna, anche la pagina resta uguale.

## Aggiornare a mano

1. Apri la scheda **Actions** del repository.
2. Scegli **Aggiornamento mensile** nella colonna a sinistra.
3. Premi **Run workflow** e conferma. Dopo un paio di minuti il sito è aggiornato.

## Pubblicazione (da fare una sola volta)

1. **Settings → Pages**.
2. In *Source* scegli **Deploy from a branch**, ramo **main**, cartella **/docs**, poi **Save**.
3. Per usare un indirizzo tipo `misure.360digitale.it`, scrivilo in *Custom domain* e crea sul pannello Aruba un record CNAME che punta a `<tuo-utente>.github.io`.

## Modificare la pagina

Grafica e funzioni stanno in `build/template.html`; il calcolo dei dati in `build/build.py`. Le modifiche si fanno chiedendo a Claude Code su questo repository: alla prossima esecuzione dell'aggiornamento (o premendo *Run workflow*) la pagina viene rigenerata.

Parametri utili in `build/build.py`:

- `ANNO_MINIMO`: primo anno incluso (ora 2020).
- `MIN_RIGHE`: se il dataset scaricato contiene meno modelli di questo numero, l'aggiornamento si ferma e il sito resta com'era.
