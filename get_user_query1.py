import psycopg
import ollama


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "abcd"
}

LLM_MODEL = "llama3.2"
EMBED_MODEL = "nomic-embed-text"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    return psycopg.connect(
        **DB_CONFIG
    )


# =========================================================
# GET TABLE SCHEMA
# =========================================================

def get_schema():

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'excel_data'
                ORDER BY ordinal_position
            """)

            return cur.fetchall()


# =========================================================
# CREATE EMBEDDING
# =========================================================

def create_embedding(text):

    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text
    )

    return response["embedding"]


# =========================================================
# CLASSIFY QUESTION
# =========================================================

def classify_question(question):

    prompt = f"""
You are ONLY a router.

Decide whether this question should be answered using:

SQL
or
VECTOR

Use SQL for:
- total
- sum
- average
- count
- highest
- lowest
- sales
- revenue
- dates
- filtering
- grouping
- comparisons
- numerical questions

Use VECTOR for:
- complaints
- feedback
- comments
- descriptions
- similar meaning
- customer issues
- delivery problems
- product problems

IMPORTANT:
The answer MUST come from PostgreSQL table excel_data.
Never answer the question yourself.

Return ONLY one word:

SQL

or

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

    result = response["message"]["content"].strip().upper()

    if "VECTOR" in result:
        return "VECTOR"

    return "SQL"


# =========================================================
# GENERATE SQL
# =========================================================

def generate_sql(question):

    schema = get_schema()

    schema_text = "\n".join(
        f"- {column}: {datatype}"
        for column, datatype in schema
        if column != "embedding"
    )

    prompt = f"""
You generate PostgreSQL SQL for a database assistant.

DATABASE:
PostgreSQL

ONLY TABLE:
excel_data

SCHEMA:
{schema_text}

USER QUESTION:
{question}

STRICT RULES:

1. The answer MUST come from excel_data.
2. Use ONLY excel_data.
3. Do NOT use model knowledge.
4. Do NOT create imaginary tables.
5. Do NOT create imaginary columns.
6. Return ONLY one SELECT statement.
7. Never INSERT.
8. Never UPDATE.
9. Never DELETE.
10. Never DROP.
11. Never ALTER.
12. Never CREATE.
13. Do not query any table except excel_data.
14. Use PostgreSQL syntax.

Return ONLY SQL.
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

    sql = response["message"]["content"].strip()

    sql = sql.replace(
        "```sql",
        ""
    )

    sql = sql.replace(
        "```",
        ""
    )

    return sql.strip()


# =========================================================
# VALIDATE SQL
# =========================================================

def validate_sql(sql):

    sql_lower = sql.lower().strip()

    if not sql_lower.startswith("select"):

        raise ValueError(
            "Only SELECT statements are allowed."
        )

    forbidden = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "create ",
        "grant ",
        "revoke "
    ]

    for word in forbidden:

        if word in sql_lower:

            raise ValueError(
                f"Forbidden SQL operation: {word}"
            )

    # Make sure excel_data is being used
    if "excel_data" not in sql_lower:

        raise ValueError(
            "Query must use excel_data."
        )


# =========================================================
# EXECUTE SQL
# =========================================================

def execute_sql(sql):

    validate_sql(sql)

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(sql)

            rows = cur.fetchall()

            columns = [
                description.name
                for description in cur.description
            ]

            return columns, rows


# =========================================================
# VECTOR SEARCH
# =========================================================

def vector_search(question):

    question_vector = create_embedding(
        question
    )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    customer_name,
                    city,
                    product,
                    sales,
                    sale_date,
                    description,
                    1 - (embedding <=> %s) AS similarity
                FROM excel_data
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT 10
                """,
                (
                    question_vector,
                    question_vector
                )
            )

            return cur.fetchall()


# =========================================================
# FINAL ANSWER
# =========================================================

def generate_final_answer(
    question,
    data
):

    prompt = f"""
You are the final response generator.

IMPORTANT:
The database results below are the ONLY source
you are allowed to use.

Do NOT use your own knowledge.

USER QUESTION:
{question}

POSTGRESQL RESULTS:
{data}

Rules:

- Answer only from the PostgreSQL results.
- Do not invent customers.
- Do not invent numbers.
- If there are no matching records, say:
  "No matching records were found in excel_data."
- Keep the answer concise.
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

    return response["message"]["content"].strip()


# =========================================================
# MAIN QUESTION FUNCTION
# =========================================================

def ask(question):

    mode = classify_question(
        question
    )

    print(
        f"\nMode selected: {mode}"
    )

    # -----------------------------------------------------
    # SQL
    # -----------------------------------------------------

    if mode == "SQL":

        sql = generate_sql(
            question
        )

        print(
            "\nGenerated SQL:"
        )

        print(sql)

        columns, rows = execute_sql(
            sql
        )

        if not rows:

            return (
                "No matching records were found "
                "in excel_data."
            )

        data = "\n".join(
            str(
                dict(
                    zip(
                        columns,
                        row
                    )
                )
            )
            for row in rows
        )

    # -----------------------------------------------------
    # VECTOR
    # -----------------------------------------------------

    else:

        rows = vector_search(
            question
        )

        if not rows:

            return (
                "No matching records were found "
                "in excel_data."
            )

        data = "\n".join(
            str({
                "customer_name": row[1],
                "city": row[2],
                "product": row[3],
                "sales": row[4],
                "sale_date": row[5],
                "description": row[6],
                "similarity": float(row[7])
            })
            for row in rows
        )

    # -----------------------------------------------------
    # FINAL LLM
    # -----------------------------------------------------

    return generate_final_answer(
        question,
        data
    )


# =========================================================
# CHAT
# =========================================================

if __name__ == "__main__":

    print(
        "PostgreSQL + pgvector + Ollama"
    )

    print(
        "Data source: excel_data"
    )

    print(
        "Type 'exit' to quit."
    )

    while True:

        question = input(
            "\nYou: "
        )

        if question.lower() == "exit":
            break

        try:

            answer = ask(
                question
            )

            print(
                "\nAI:",
                answer
            )

        except Exception as e:

            print(
                "\nERROR:",
                e
            )
