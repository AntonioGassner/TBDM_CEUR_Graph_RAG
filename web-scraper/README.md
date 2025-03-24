## Prerequisites

Before running the script, ensure you have the following installed:

- Python 3.8 or higher
- MongoDB (e.g. MongoDB Atlas)
- Required Python packages (listed in `requirements.txt`)

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/AronOehrli/TBDM-CEUR-WS.git
    cd TBDM-CEUR-WS/web-scraper
    ```

2. **Create and activate a virtual environment**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

Create a `.env` file in the `web-scraper` directory and add the following environment variables:

```env
BASE_URL = "https://ceur-ws.org/"
MONGO_URI = "mongodb://localhost:27017/" # Replace with the actual URI
DB_NAME = "ceur_ws"
```

## Running the Script

To run the script, execute the following command:

```sh
python main.py
```

Logs can be analyzed and found in `scraping.log`.