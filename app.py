from website import start
from dotenv import load_dotenv
import os

load_dotenv()

SERVER_PORT = os.environ.get("FLASK_SERVER_PORT", 5000)

app = start()

if(__name__ == "__main__"):
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=True)