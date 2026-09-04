import ollama
import psycopg

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "abcd"
}

EMBED_MODEL = "nomic-embed-text"


def create_embedding(text):

    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text
    )

    return response["embedding"]


def create_embeddings():

    with psycopg.connect(
        **DB_CONFIG
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    customer_name,
                    city,
                    product,
                    description
                FROM excel_data
                WHERE embedding IS NULL
                """
            )

            rows = cur.fetchall()

            print(
                f"Rows to embed: {len(rows)}"
            )

            for row in rows:

                row_id = row[0]

                text = f"""
Customer: {row[1]}
City: {row[2]}
Product: {row[3]}
Description: {row[4]}
"""

                vector = create_embedding(
                    text
                )

                cur.execute(
                    """
                    UPDATE excel_data
                    SET embedding = %s
                    WHERE id = %s
                    """,
                    (
                        vector,
                        row_id
                    )
                )

                print(
                    f"Embedded row {row_id}"
                )

        conn.commit()


if __name__ == "__main__":
    create_embeddings()
