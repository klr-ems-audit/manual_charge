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
