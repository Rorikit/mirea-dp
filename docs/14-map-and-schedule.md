# Карта и расписание

## Карта

MVP использует статичное растровое изображение PNG/WebP: это безопаснее SVG, проще подготовить и поддержать pinch zoom/pan. Upload декодируется и повторно кодируется сервером, проверяются MIME/signature, ≤10 MiB, ≤20 000×20 000 px и decompression limit. Файл получает generated name, immutable hash URL; публикация новой версии атомарно переключает active asset. Оригинальное имя — только metadata. `MapZone` остаётся неактивной схемой расширения.

## Расписание

`ScheduleItem(event_id,title,description,location,starts_at,ends_at,display_order,is_published,map_zone_id,created_at,updated_at)`. CHECK `ends_at > starts_at`; индекс `(event_id,is_published,starts_at,display_order)`. API возвращает `server_time` и timezone. Статусы: `COMPLETED` при now≥end; `NOW` при start≤now<end; `NEXT` — один ближайший будущий по `(starts_at,display_order)`; остальные `SCHEDULED`. Пересечения допустимы как параллельные активности. Только published доступно public.

