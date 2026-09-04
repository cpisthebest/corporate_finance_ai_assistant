import psycopg


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "abcd"
}


def get_connection():
    return psycopg.connect(
        **DB_CONFIG
    )


def get_schema():

    with get_connection() as conn, conn.cursor() as cur:

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


def execute_select(sql):

    sql_lower = sql.lower().strip()

    # Security
    if not sql_lower.startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed"
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
                f"Forbidden SQL: {keyword}"
            )

    # Make sure AI is using our table
    if "excel_data" not in sql_lower:
        raise ValueError(
            "SQL must query excel_data"
        )

    with get_connection() as conn, conn.cursor() as cur:

        cur.execute(sql)

        rows = cur.fetchall()

        columns = [
            d.name
            for d in cur.description
        ]

        return columns, rows

def vector_search(question_vector):

    with get_connection() as conn, conn.cursor() as cur:

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
                    1 - (embedding <=> %s::vector) AS similarity
                FROM excel_data
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT 10
                """,
            (
                question_vector,
                question_vector
            )
        )

        return cur.fetchall()
