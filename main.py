from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Zezwalaj frontendowi na dostęp
origins = [
    "http://localhost:3000",  # Twój frontend
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # albo ["*"] dla wszystkich źródeł (niezalecane w produkcji)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@db:5432/notesdb"
engine = create_engine(DATABASE_URL, echo=True)

class Note(BaseModel):
    title: str
    content: str

@app.on_event("startup")
def startup():
    # upewniamy się, że tabela istnieje
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/notes")
def get_notes():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, title, content FROM notes"))
        notes = [{"id": row.id, "title": row.title, "content": row.content} for row in result]
    return notes

@app.post("/notes")
def add_note(note: Note):
    with engine.connect() as conn:
        result = conn.execute(
            text("INSERT INTO notes (title, content) VALUES (:title, :content) RETURNING id"),
            {"title": note.title, "content": note.content}
        )
        note_id = result.scalar()
        conn.commit()
    return {"id": note_id, "title": note.title, "content": note.content}

