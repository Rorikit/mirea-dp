# ADR-009: Формат карты

- Статус: принято
- Решение MVP: server-decoded/re-encoded PNG/WebP высокого разрешения с zoom/pan, versioned immutable URL. SVG/MapZone отложены.
- Причина: меньше XSS/active-content риска, проще авторинг и mobile rendering. Цена — нет интерактивных зон и хуже масштабирование текста.

