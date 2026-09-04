import ollama

from database import get_schema


LLM_MODEL = "llama3.2"
EMBED_MODEL = "nomic-embed-text"


def create_embedding(text):

    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text
    )

    return response["embedding"]


def classify_question(question):

    prompt = f"""
You are a routing system.

You have ONLY two choices:

SQL
VECTOR

Use SQL for:
- totals
- sales
- revenue
- counts
- averages
- dates
- filtering
- grouping
- ranking
- numerical calculations
- sum

Use VECTOR for:
- complaints
- customer feedback
- descriptions
- delivery problems
- product problems
- similar text
- semantic questions

IMPORTANT:
Do not answer the question.

Return only:
SQL

or:
VECTOR

Question:
{question}
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response[
        "message"
    ][
        "content"
    ].strip().upper()

    if "VECTOR" in result:
        return "VECTOR"

    return "SQL"


def generate_sql(question):

    schema = get_schema()

    schema_text = "\n".join(
        f"{column}: {datatype}"
        for column, datatype in schema
        if column != "embedding"
    )

    prompt = f"""
You are a PostgreSQL SQL generator.

DATABASE:
PostgreSQL

ONLY TABLE:
excel_data

SCHEMA:
{schema_text}

USER QUESTION:
{question}

STRICT RULES:

1. Use ONLY excel_data.
2. Do not use any other table.
3. Do not use model knowledge.
4. Return ONE SELECT query.
5. Never INSERT.
6. Never UPDATE.
7. Never DELETE.
8. Never DROP.
9. Never ALTER.
10. Never CREATE.
11. Use exact column names.
12. Return ONLY SQL.
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    sql = response[
        "message"
    ][
        "content"
    ].strip()

    sql = sql.replace(
        "```sql",
        ""
    ).replace(
        "```",
        ""
    )

    return sql.strip()

def generate_final_answer(
    question,
    database_result
):

    prompt = f"""
You are a PostgreSQL data assistant.

The following records were retrieved from
PostgreSQL table excel_data.

They were first retrieved using pgvector
and then reranked using FlashRank.

These records are your ONLY source of information.

USER QUESTION:
{question}

RERANKED DATABASE RECORDS:
{database_result}

STRICT RULES:

1. Answer ONLY using the records above.
2. Do NOT use your pretrained knowledge.
3. Do NOT invent customers.
4. Do NOT invent numbers.
5. Do NOT assume information not present.
6. If the records do not contain enough information,
   say that no sufficient information was found.
7. Keep the answer concise.
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response[
        "message"
    ][
        "content"
    ].strip()

