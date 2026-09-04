import pandas as pd
import psycopg

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "abcd"
}


def import_excel(file_path):

    df = pd.read_excel(
        file_path
    )

    # Clean column names
    df.columns = [
        str(col)
        .strip()
        .lower()
        .replace(" ", "_")
        for col in df.columns
    ]

    # Convert dates
    if "sale_date" in df.columns:

        df["sale_date"] = pd.to_datetime(
            df["sale_date"],
            errors="coerce"
        ).dt.date

    # Replace NaN with None
    df = df.where(
        pd.notna(df),
        None
    )

    records = []

    for row in df.itertuples(
        index=False,
        name=None
    ):

        records.append(row)

    with psycopg.connect(
        **DB_CONFIG
    ) as conn:

        with conn.cursor() as cur:

            with cur.copy(
                """
                COPY excel_data (
                    customer_name,
                    city,
                    product,
                    sales,
                    sale_date,
                    description
                )
                FROM STDIN
                """
            ) as copy:

                for row in records:

                    copy.write_row(row)

        conn.commit()

    print(
        f"Imported {len(df):,} rows"
    )


if __name__ == "__main__":

    import_excel(
        "data.xlsx"
    )
