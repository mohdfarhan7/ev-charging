# EV Charging Station API

A FastAPI-based EV charging station management system implementing OCPP 1.6 protocol.

## Features

- OCPP 1.6 protocol implementation
- WebSocket server for charger communication
- REST API endpoints for charger management
- Real-time charger status monitoring
- Session management
- Third-party API integration

## Deployment on Render

1. Fork this repository to your GitHub account
2. Sign up for a Render account at https://render.com
3. Click "New +" and select "Web Service"
4. Connect your GitHub repository
5. Configure the service:
   - Name: ev-charger-api
   - Environment: Docker
   - Branch: main
   - Plan: Free
6. Click "Create Web Service"

The application will be deployed and accessible at a public URL.

## Local Development

```bash
git clone <your-repo-url>
cd ev-charging
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 10000 --reload
