# Manual Charge

Moduł Home Assistant do sterowania ładowaniem magazynu energii

w falownikach Deye. Część ekosystemu **KLR EMS Audit System**.

> ⚠️ Wersja wczesna (0.1.x) — interfejs może ulec zmianie.

![Karta dashboardu](https://raw.githubusercontent.com/klr-ems-audit/manual_charge/main/images/daschboard_manu_charge.png

)

## Do czego służy

Moduł blokuje ładowanie magazynu (ustawia prąd ładowania na 0 A)

w zadanych oknach czasowych — na przykład po to, by nadwyżka produkcji

z paneli trafiła do sieci zamiast do akumulatorów.

Przed wyzerowaniem zapamiętuje bieżący prąd ładowania i przywraca go

po ustaniu blokady.

## Instalacja przez HACS

1. HACS → menu (⋮) → **Custom repositories**

2. Wklej adres repozytorium:

https://github.com/klr-ems-audit/manual_charge

3. Kategoria: **Integration** → **Add**
4. Wyszukaj „Manual Charge" → **Download**
5. Zrestartuj Home Assistant
6. Ustawienia → Urządzenia i usługi → **Dodaj integrację** → „Manual Charge"

## Konfiguracja

Kreator poprosi o wskazanie dwóch encji Twojego falownika:

| Pole | Czego szukać | Przykład |
|---|---|---|
| Encja maksymalnego prądu ładowania | encja `number.` sterująca prądem ładowania magazynu | `number.deye_battery_max_charging_current` |
| Sensor naładowania magazynu (SOC) | sensor `sensor.` z poziomem naładowania w % | `sensor.deye_battery` |

Nazwy zależą od użytej integracji falownika (np. Solarman, Deye Modbus).
Opcjonalnie możesz włączyć powiadomienia systemowe przy zmianie stanu blokady.

Ustawienia można zmienić później: Urządzenia i usługi → Manual Charge →
**Konfiguruj**.

## Karta dashboardu

W repozytorium znajduje się gotowa karta: [`dashboard_card.yaml`](dashboard_card.yaml).

Dashboard → Edytuj → Dodaj kartę → **Ręcznie** → wklej zawartość pliku.

Nie jest obowiązkowa — wszystkie encje znajdziesz też na automatycznej
stronie urządzenia (Ustawienia → Urządzenia i usługi → Urządzenia →
Manual Charge).

## Jak działa blokada

Prąd ładowania jest zerowany, gdy spełniony jest którykolwiek z warunków:

- włączono **Zablokuj natychmiast**, albo
- **Harmonogram aktywny** jest włączony, a bieżący czas mieści się
  w aktywnym terminie **i** naładowanie magazynu przekracza próg SOC
  tego terminu.

**Próg SOC działa jako „blokuj powyżej".** Przy progu 31% blokada zadziała
dopiero, gdy magazyn będzie naładowany ponad 31% — poniżej tej wartości
ładowanie przebiega normalnie, mimo trwającego okna czasowego.

Okno o identycznej godzinie początku i końca jest traktowane jako
**nieaktywne**. Okna mogą przechodzić przez północ (np. 22:00–06:00).

Po ustaniu blokady przywracany jest zapamiętany prąd. Jeśli nie ma
zapamiętanej wartości, używany jest **prąd powrotu**.

Stan jest uzgadniany co minutę, po starcie Home Assistant, po zmianie
naładowania magazynu oraz po powrocie falownika do dostępności —
restart w trakcie blokady nie zostawi falownika z zerowym prądem.

> **Uwaga:** „Zablokuj natychmiast" celowo wyłącza się po restarcie
> Home Assistant (samorozbrojenie). Pozostałe ustawienia są odtwarzane.

## Eksport nadwyżki do sieci

Zablokowanie ładowania powoduje, że nadwyżka produkcji trafia do sieci.
Zachowanie zależy jednak od ustawień samego falownika — jeżeli eksport
został ograniczony lub wyłączony po stronie urządzenia (parametry
`Solar Sell`, `Max Sell Power`), efektem będzie samo ograniczenie
ładowania, bez sprzedaży energii.

## Zdarzenia

Moduł emituje zdarzenie `manu_charge_blocking_changed` przy każdej
zmianie prądu ładowania — możesz podpiąć pod nie własne automatyzacje.

Dane zdarzenia: `entry_id`, `blocking`, `previous_current`, `target_current`.

## Rozwiązywanie problemów

**Nie widzę integracji na liście po instalacji**
Upewnij się, że Home Assistant został zrestartowany po pobraniu z HACS.

**Encje pokazują `unavailable`**
Sprawdź, czy wskazane w konfiguracji encje falownika są dostępne.
Moduł nie wykonuje żadnych zmian, dopóki falownik nie odpowiada.

**Prąd nie wraca po zakończeniu okna**
Sprawdź wartość **Prąd powrotu** — jeśli wynosi 0, moduł nie ma do czego
wracać. Ustaw wartość odpowiednią dla swojej instalacji.

**Szczegółowe logi**
Dodaj do `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.manu_charge: debug
```

## Licencja

MIT — patrz [LICENSE](LICENSE).





# Manual Charge

Moduł Home Assistant do ręcznego sterowania ładowaniem magazynu energii
w falownikach Deye. Część ekosystemu **KLR EMS Audit System**.

> ⚠️ Wersja wczesna (0.1.x) — interfejs może ulec zmianie.

## Instalacja przez HACS

1. HACS → Integrations → menu (⋮) → **Custom repositories**
2. Dodaj `https://github.com/klr-ems-audit/manual_charge`, kategoria **Integration**
3. Wyszukaj „Manual Charge" → **Download**
4. Zrestartuj Home Assistant
5. Ustawienia → Urządzenia i usługi → **Dodaj integrację** → „Manual Charge"

## Instalacja ręczna

Skopiuj katalog `custom_components/manu_charge` do swojego `custom_components/`
i zrestartuj Home Assistant.

## Licencja

MIT — patrz [LICENSE](LICENSE).

## Karta dashboardu

W repozytorium znajduje się gotowa karta: [`dashboard_card.yaml`](dashboard_card.yaml).

Dashboard → Edytuj → Dodaj kartę → **Ręcznie** → wklej zawartość pliku.

## Jak działa blokada

Moduł ustawia prąd ładowania magazynu na **0 A**, gdy spełniony jest
którykolwiek z warunków:

- włączono **Zablokuj natychmiast**, albo
- **Harmonogram aktywny** jest włączony, a bieżący czas mieści się
  w aktywnym terminie **i** naładowanie magazynu przekracza próg SOC tego terminu.

Przed wyzerowaniem moduł zapamiętuje bieżący prąd ładowania i przywraca go
po ustaniu blokady. Jeśli nie ma zapamiętanej wartości, używa **prądu powrotu**.

Stan jest uzgadniany co minutę, po starcie Home Assistant oraz po powrocie
falownika do dostępności — zgubiona zmiana stanu nie zostawi falownika
w niewłaściwym trybie.

> **Uwaga:** „Zablokuj natychmiast" celowo wyłącza się po restarcie
> Home Assistant (samorozbrojenie). Pozostałe ustawienia są odtwarzane.
