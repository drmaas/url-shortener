import uvicorn
import os

if __name__ == "__main__":
    os.environ.setdefault("TABLE_NAME", "UrlShortenerTable")
    uvicorn.run("local:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8080)), reload=True)
