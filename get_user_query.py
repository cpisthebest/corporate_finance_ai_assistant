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


def get_schema():

    with psycopg.connect(
        **DB_CONFIG
    ) as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_name = 'excel_data'
                ORDER BY ordinal_position
            """)

            return cur.fetchall()


def generate_sql(question):

    columns = get_schema()

    schema = "\n".join(
        f"{column}: {datatype}"
        for column, datatype in columns
    )

    prompt = f"""
You are a PostgreSQL expert.

Database table:

excel_data

Columns:
{schema}

Generate ONE PostgreSQL SELECT query
that answers the user's question.

Rules:
- Return ONLY SQL.
- Do not use markdown.
- Only SELECT statements are allowed.
- Never INSERT, UPDATE, DELETE, DROP, ALTER or CREATE.
- Use the exact column names provided.
- Use SUM for totals.
- Use COUNT for counts.
- Use AVG for averages.
- Use GROUP BY for grouped results.
- Use ORDER BY for rankings.
- Use PostgreSQL syntax.

User question:

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

    sql = response["message"]["content"].strip()

    # Remove markdown if Ollama returns it
    sql = sql.replace(
        "```sql",
        ""
    ).replace(
        "```",
        ""
    ).strip()

    return sql


def validate_sql(sql):

    sql_lower = sql.lower().strip()

    if not sql_lower.startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed."
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

    for keyword in forbidden:

        if keyword in sql_lower:

            raise ValueError(
                f"Forbidden SQL operation: {keyword}"
            )


def execute_sql(sql):

    validate_sql(sql)

    with psycopg.connect(
        **DB_CONFIG
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(sql)

            rows = cur.fetchall()

            columns = [
                desc.name
                for desc in cur.description
            ]

            return columns, rows


def generate_answer(
    question,
    columns,
    rows
):

    result = "\n".join(
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

    prompt = f"""
You are an AI data assistant.

Answer the user's question using the
PostgreSQL query result.

Question:
{question}

Query result:
{result}

Rules:
- Do not invent information.
- Use the exact numbers from the result.
- Be concise.
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

    return response["message"]["content"]


def ask(question):

    sql = generate_sql(
        question
    )

    print("\nSQL:")
    print(sql)

    columns, rows = execute_sql(
        sql
    )

    answer = generate_answer(
        question,
        columns,
        rows
    )

    return answer


if __name__ == "__main__":

    print(
        "PostgreSQL + pgvector + Ollama"
    )

    while True:

        question = input(
            "\nAsk: "
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
