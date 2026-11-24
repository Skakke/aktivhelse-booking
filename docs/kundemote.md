# Kundemøte – AktivHelse Treningssenter AS

Gjennomført skriftlig i Teams, november 2026. Faglærer svarte i rollen som kunde.

## Første henvendelse

> Hei!
> I forbindelse med oppdraget fra dere ønsker jeg å avklare noen saker rundt utvikling av gruppetime booking.
> Alle muligheter er åpne for at jeg skal kunne lage en løsning som er tilfredsstillende for både ledelse, instruktører og deltakere.
>
> 1. Er det slik i dag at dere har lister på papir for dette? Eller hvordan løses det i dag?
> 2. Hvem skal kunne legge til deltakere? De som holder timene eller medlemmene selv?
> 3. Ønsker dere en nettside som alle skal kunne gå inn på og signe opp? Eller en vindusapp som kjører i resepsjonen for eksempel?
> 4. Har dere noen spesielle krav rundt funksjonalitet? Som for eksempel bekreftelse på e-post eller SMS? Avmelding fra timer? Varsler?
>
> Kom tilbake til meg så kan vi planlegge dette grundig.

## Tilleggsspørsmål

> 1. Hvor oppstår dobbeltbookinger og misforståelser oftest i dag, og hvilke konsekvenser får det for dere og medlemmene?
> 2. Hvordan fungerer kapasiteten på gruppetimene, og varierer den mellom sal, timetype og de tre avdelingene?
> 3. Hva ønsker dere skal skje når en time er fullbooket?
> 4. Hvordan bør medlemmene identifisere seg ved påmelding, og hvilke opplysninger trenger dere om deltakerne?
> 5. Hva må den første versjonen kunne for at dere skal oppleve at konseptet fungerer, og hva kan vente til senere?
> 6. Hvilke regler bør gjelde for avmelding, for eksempel en frist før timen starter?

## Kundens svar

| Tema | Kundens svar | Konsekvens for løsningen |
| --- | --- | --- |
| Dagens situasjon | Manuelle lister og henvendelser til resepsjonen. Gir manglende oversikt, dobbeltpåmeldinger og misforståelser om ledig kapasitet. | Ett felles system med sanntidsoversikt over plasser. |
| Brukere og roller | Medlemmer melder seg på og av selv. Ansatte ser deltakerlister, administrerer påmeldinger og har oversikt over kapasitet. | Medlemssider + adminside. Ansatte kan også melde på og fjerne deltakere. |
| Teknologi | Ingen krav til nett eller vindusapp. Utvikler vurderer og begrunner. | Nettløsning: fungerer på mobil, PC og i resepsjonen uten installasjon. |
| Kapasitet | Varierer mellom timer, saler og avdelinger. Skal oppdateres automatisk og hindre overbooking og dobbeltpåmelding. | Kapasitet og sal per time. Radlås i databasen og unik nøkkel per medlem og time. |
| Fullbookede timer | Skal vises tydelig, og videre påmelding skal ikke være mulig. Venteliste kan vurderes senere. | «Fullt»-merke og ingen påmeldingsknapp. Venteliste er fremtidig funksjonalitet. |
| Medlemsopplysninger | Navn og medlemsnummer er nok i første versjon. | Medlemsnummer erstatter e-post som identifikasjon. |
| Avmelding | Plassen skal automatisk bli ledig. Utvikler kan foreslå frist. | Avmeldingsfrist 2 timer før start (kan endres). Ansatte kan alltid fjerne deltakere. |
| Varslinger | Ønskelig på sikt, ikke nødvendig i prototypen. | Fremtidig funksjonalitet. |
| Første versjon | Avdelingsvalg, timeoversikt, påmelding, avmelding, kapasitetskontroll og administrasjon for ansatte. | Alle er må-krav i prototypen. |

## Faglig tilbakemelding fra faglærer

Spørsmålene ble vurdert som gode og åpne. Anbefaling for kravspesifikasjonen: skille tydelig mellom
funksjonelle og ikke-funksjonelle krav, og mellom må-krav, bør-krav og fremtidig funksjonalitet.
Løsningen skal dekke kundens faktiske behov, fungere stabilt og ha begrunnede tekniske valg.
