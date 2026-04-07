# server/app.py

from server.main import app


def main():
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()