PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS display_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('time', 'date', 'animation', 'message', 'todo')),
    config TEXT DEFAULT '{}',
    duration INTEGER,
    sort_order INTEGER NOT NULL DEFAULT 0,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    done INTEGER DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_display_items_sort ON display_items(sort_order);
CREATE INDEX IF NOT EXISTS idx_todos_sort ON todos(sort_order);
