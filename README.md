# Occlusmart Backend

This is the FastAPI backend for the Occlusmart application, which handles image uploads and analysis.

## Setup

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /api/health` - Check if the server is running

### Analyze Occlusion
- `POST /api/analyze-occlusion` - Upload and analyze pre-op and during-op images
  - Form data:
    - `pre_op`: Pre-operation image file
    - `during_op`: During-operation image file

## Development

### Testing the API
You can test the API using tools like [Postman](https://www.postman.com/) or `curl`:

```bash
curl -X POST "http://localhost:8000/api/analyze-occlusion" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "pre_op=@/path/to/pre_op.jpg" \
  -F "during_op=@/path/to/during_op.jpg"
```

## Deployment

For production deployment, consider using:
- Gunicorn with Uvicorn workers
- Nginx as a reverse proxy
- Environment variables for configuration
- Proper SSL/TLS setup

## License

MIT
