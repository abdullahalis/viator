from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()
app = FastAPI()

@app.post("/query")
async def query(query: str):
    """
    Endpoint to handle queries.
    """
    # Here you would typically process the query and return a response.
    # For now, we just return the query as a demonstration.
    return {"query": query}