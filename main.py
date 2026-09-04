from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database import execute_select, vector_search
from ollama_service import (
    classify_question,
    create_embedding,
    generate_final_answer,
    generate_sql,
)
from rerank import rerank

app = FastAPI(
    title="Excel AI Assistant",
    version="1.0"
)


class QuestionRequest(BaseModel):

    question: str


@app.get("/")
def home():

    return {
        "message": "Excel AI Assistant API",
        "database": "postgres",
        "vector": "pgvector",
        "llm": "Ollama"
    }


@app.post("/ask")
def ask_question(
    request: QuestionRequest
):
    
    question = request.question.strip()
    print(question)
    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:

        # ==================================================
        # ROUTE QUESTION
        # ==================================================

        mode = classify_question(
            question
        )


        # ==================================================
        # SQL MODE
        # ==================================================

        if mode == "SQL":

            sql = generate_sql(
                question
            )

            columns, rows = execute_select(
                sql
            )

            if not rows:

                return {
                    "question": question,
                    "mode": "SQL",
                    "sql": sql,
                    "answer":
                        "No matching records were found."
                }

            result = [
                dict(
                    zip(
                        columns,
                        row
                    )
                )
                for row in rows
            ]

            answer = generate_final_answer(
                question,
                result
            )

            return {
                "question": question,
                "mode": "SQL",
                "sql": sql,
                "data": result,
                "answer": answer
            }


        # ==================================================
        # VECTOR MODE
        # ==================================================

        question_vector = create_embedding(
            question
        )

        rows = vector_search(
            question_vector,limit=50
        )
        
        if not rows:

            return {
                "question": question,
                "mode": "VECTOR",
                "answer":
                    "No matching records were found."
            }


        result = []

        # for row in rows:

        #     result.append({
        #         "id": row[0],
        #         "customer_name": row[1],
        #         "city": row[2],
        #         "product": row[3],
        #         "sales": float(row[4])
        #             if row[4] is not None
        #             else None,
        #         "sale_date": str(row[5])
        #             if row[5]
        #             else None,
        #         "description": row[6],
        #         "similarity": float(row[7])
        #     })

        documents = []

        for row in rows:

            text = f"""
            Customer: {row[1]}
            City: {row[2]}
            Product: {row[3]}
            Sales: {row[4]}
            Date: {row[5]}
            Description: {row[6]}
            """

            documents.append(text)
        print("Documents -> ",documents)
        reranked = rerank(
        question,
        documents,
        top_k=5
        )

        context=[]
        for item in reranked:
            context.append(item["text"])

        answer = generate_final_answer(
            question,
            context
        )

        return {
            "question": question,
            "mode": "VECTOR",
            "data": context,
            "answer": answer
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
