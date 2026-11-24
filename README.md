# AktivHelse – booking av gruppetimer

Prototype av et bookingsystem for gruppetimer hos AktivHelse Treningssenter AS.
Medlemmer ser timeplanen og melder seg på eller av. Ansatte oppretter timer og ser deltakerlister.

## Start løsningen

Krav: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (eller Docker Engine med Compose).

```bash
docker compose up --build
```

Åpne <http://localhost:8000>.

Løsningen starter med testdata for de neste sju dagene, blant annet én time som er full.
Databasen ligger kun i minnet, så alle endringer forsvinner når du stopper med `Ctrl+C`
eller `docker compose down`. Neste oppstart gir ferske testdata.

| Side | Adresse |
| --- | --- |
| Timeplan og påmelding | <http://localhost:8000/> |
| Mine påmeldinger (avmelding) | <http://localhost:8000/mine> – prøv medlemsnummer `100003` |
| Administrasjon | <http://localhost:8000/admin> |
| API-dokumentasjon | <http://localhost:8000/docs> |

## Kjør testene

Med løsningen kjørende, i et nytt terminalvindu:

```bash
docker compose exec app pytest
```

Testene bruker en egen testdatabase og påvirker ikke demodataene.
Testen `test_concurrent_bookings_never_overbook` sender 20 samtidige påmeldinger til en time med
3 plasser og kontrollerer at nøyaktig 3 går gjennom.

### Manuell test

1. Meld deg på en time. Antall ledige plasser går ned med én gang.
2. Prøv å melde deg på samme time igjen med samme medlemsnummer. Det avvises.
3. Send skjemaet med tomt navn eller ugyldig medlemsnummer. Du får norske feilmeldinger.
4. Prøv timen merket «Fullt». Den har ingen påmeldingsknapp.
5. Gå til «Mine påmeldinger», skriv inn medlemsnummeret ditt og meld deg av. Timer som starter om
   under 2 timer kan ikke meldes av (avmeldingsfrist).
6. Gå til «Admin», opprett en ny time og se at den dukker opp i timeplanen.
7. Åpne en time i «Admin» og meld på et medlem som ansatt.

## Teknologi

| Del | Valg |
| --- | --- |
| Backend og API | Python 3.13, FastAPI |
| Frontend | Jinja2-maler, HTMX, egen CSS |
| Database | PostgreSQL 17, SQLAlchemy 2 (ORM), Alembic (migreringer) |
| Test | pytest |
| Kjøring | Docker Compose |

Begrunnelsen for valgene står i kravspesifikasjonen.

### Hvordan overbooking hindres

Ved påmelding låses raden for timen med `SELECT … FOR UPDATE` før ledige plasser telles
(`app/services.py`, funksjonen `book`). Kommer to påmeldinger på siste plass samtidig, må den
andre vente til den første er ferdig, og ser da at timen er full. En unik nøkkel på
(time, medlemsnummer) i databasen hindrer i tillegg dobbeltpåmelding.

## Innstillinger

| Miljøvariabel | Standard | Betydning |
| --- | --- | --- |
| `CANCEL_DEADLINE_HOURS` | `2` | Hvor mange timer før start medlemmer kan melde seg av |

## Prosjektstruktur

```
app/
  main.py          oppstart og ruter
  models.py        databasetabeller (ORM)
  schemas.py       validering av inndata
  services.py      forretningslogikk: påmelding, kapasitet, avmelding
  routers/         public.py (medlemmer), admin.py (ansatte), api.py (JSON)
  templates/       HTML-maler
  static/          CSS og HTMX
migrations/        databasemigreringer (Alembic)
tests/             automatiske tester
compose.yaml       oppstart for demo/innlevering (uten lagring)
compose.dev.yaml   tillegg for utvikling (lagring på disk, auto-reload)
docs/              kundemøte og annen dokumentasjon
```

## Utvikling

For utvikling lagres databasen i `./data/postgres` på maskinen, og appen lastes inn på nytt når koden endres:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Databasen er da også tilgjengelig på `localhost:5432` (bruker og passord: `booking`).
Slett mappen `data/` for å starte med tom database.

Ny migrering etter endring i `app/models.py`:

```bash
docker compose exec app alembic revision --autogenerate -m "beskrivelse"
```

## Avgrensning

Prototypen har ikke innlogging, betaling, venteliste, e-post/SMS-varsler eller integrasjon mot
medlemssystem. Medlemsnummer antas å være 4–10 siffer og sjekkes ikke mot et medlemsregister.
Se kravspesifikasjonen for detaljer.
