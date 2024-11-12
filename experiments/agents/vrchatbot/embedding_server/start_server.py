import uvicorn

if __name__ == "__main__":
    # Run the FastAPI app, assuming your server code is saved in a file called 'embedding_server.py'
    uvicorn.run("embedding_server:app", host="127.0.0.1", port=8608, reload=True)
