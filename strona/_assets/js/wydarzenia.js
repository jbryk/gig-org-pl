/* Geodezyjna Izba Gospodarcza — dane wydarzeń (nadchodzące wydarzenia).
   Edytuj tę tablicę, aby dodać/usunąć wydarzenia. Przeszłe (date < dziś) znikają automatycznie.
   Pola:
     date      — data ISO "YYYY-MM-DD" (sortowalna; gdy znany tylko miesiąc, użyj 1. dnia miesiąca)
     dateLabel — ładny zapis daty po polsku, np. "15 września 2026" lub "Czerwiec 2027"
     title     — tytuł wydarzenia
     place     — miejsce (może być "")
     teaser    — krótka zajawka (1–2 zdania)
     link      — URL do szczegółów lub "" (brak)
*/
window.GIG_WYDARZENIA = [
  {
    date: "2027-06-01",
    dateLabel: "Czerwiec 2027",
    title: "XXXIV Walne Zgromadzenie Członków GIG",
    place: "Śląsk",
    teaser: "Kolejne Walne Sprawozdawcze Zgromadzenie Członków Geodezyjnej Izby Gospodarczej odbędzie się na Śląsku. Dokładny termin i miejsce podamy wkrótce.",
    link: ""
  }
];
