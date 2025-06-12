import sqlite3
import datetime

DB_NAME = "translator.db"


def init_db():
    """
    Initializes the database and creates the necessary tables if they don't exist.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create vocabulary table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_text TEXT NOT NULL,
        language TEXT NOT NULL,
        translated_text TEXT NOT NULL,
        annotation TEXT
    )
    """)

    # Create translation_history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS translation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_text TEXT NOT NULL,
        from_lang TEXT NOT NULL,
        to_lang TEXT NOT NULL,
        translated_text TEXT NOT NULL,
        timestamp DATETIME NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def add_translation_to_history(source_text, from_lang, to_lang, translated_text):
    """
    Adds a new translation record to the history table and returns the newly created record.
    """
    conn = sqlite3.connect(DB_NAME)
    # Use a dictionary-based row factory to make returning the new row easier
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()

    cursor.execute(
        "INSERT INTO translation_history (source_text, from_lang, to_lang, translated_text, timestamp) VALUES (?, ?, ?, ?, ?)",
        (source_text, from_lang, to_lang, translated_text, timestamp)
    )
    new_id = cursor.lastrowid
    conn.commit()

    # Fetch the newly created record
    cursor.execute("SELECT * FROM translation_history WHERE id = ?", (new_id,))
    new_history_item = dict(cursor.fetchone())

    conn.close()
    return new_history_item


def get_translation_history():
    """
    Retrieves all translation history records, ordered by the most recent first.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM translation_history ORDER BY timestamp DESC")
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history


def delete_translation_history(item_id: int):
    """Deletes a specific history record by its ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM translation_history WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_vocabulary():
    """
    Retrieves all vocabulary records.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vocabulary ORDER BY source_text")
    vocabulary = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return vocabulary


def get_vocabulary_for_lang(language: str):
    """
    Retrieves all vocabulary records for a specific target language.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT source_text, translated_text FROM vocabulary WHERE language = ?", (language,))
    vocabulary = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return vocabulary


def add_vocabulary_term(source_text, language, translated_text, annotation):
    """Adds a new term to the vocabulary table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vocabulary (source_text, language, translated_text, annotation) VALUES (?, ?, ?, ?)",
        (source_text, language, translated_text, annotation)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id}


def update_vocabulary_term(item_id, translated_text, annotation):
    """Updates an existing vocabulary term."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE vocabulary SET translated_text = ?, annotation = ? WHERE id = ?",
        (translated_text, annotation, item_id)
    )
    conn.commit()
    conn.close()


def delete_vocabulary_term(item_id):
    """Deletes a term from the vocabulary table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vocabulary WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# You can add more functions here for vocabulary CRUD operations later
# e.g., add_vocabulary_term, delete_vocabulary_term, update_vocabulary_term
