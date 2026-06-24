/* Geodezyjna Izba Gospodarcza — dane wydarzeń (nadchodzące wydarzenia).
   Edytuj tę tablicę, aby dodać/usunąć wydarzenia. Przeszłe (date < dziś) znikają automatycznie.
   Pola:
     date      — data ISO "YYYY-MM-DD" (sortowalna; gdy znany tylko miesiąc, użyj 1. dnia miesiąca)
     dateLabel — ładny zapis daty po polsku, np. "30 czerwca 2026" lub "Wrzesień 2026"
     title     — tytuł wydarzenia
     place     — miejsce (może być "")
     teaser    — krótka zajawka (1–2 zdania)
     link      — URL do szczegółów lub "" (brak)
*/
window.GIG_WYDARZENIA = [
  {
    date: "2026-06-30",
    dateLabel: "30 czerwca 2026",
    title: "Spotkanie online członków GIG",
    place: "Online",
    teaser: "Spotkanie online dla członków Geodezyjnej Izby Gospodarczej — bieżące sprawy Izby, informacje branżowe i dyskusja.",
    link: ""
  },
  {
    date: "2026-09-01",
    dateLabel: "Wrzesień 2026",
    title: "Szkolenie online: zmiany w ustawie Prawo geodezyjne i kartograficzne",
    place: "Online",
    teaser: "Szkolenie online poświęcone planowanym zmianom w ustawie Prawo geodezyjne i kartograficzne. Dokładny termin podamy wkrótce.",
    link: ""
  },
  {
    date: "2027-06-01",
    dateLabel: "Czerwiec 2027",
    title: "Walne Zebranie Członków GIG",
    place: "Katowice",
    teaser: "Doroczne Walne Zebranie Członków Geodezyjnej Izby Gospodarczej odbędzie się w Katowicach. Dokładny termin podamy wkrótce.",
    link: ""
  }
];
