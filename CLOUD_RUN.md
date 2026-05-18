# Deploy Analytics MCP to Cloud Run

This repository includes a `main.py` web entry point that serves the MCP server
over **Streamable HTTP** at `/mcp`, which is suitable for Cloud Run.

## 1. Prerequisites

- `gcloud` CLI authenticated to your Google Cloud project.
- A Google Cloud project with billing enabled.
- Access to Google Analytics properties from the identity used by Cloud Run:
  - If you deploy with a service account, add that service account email to your
    GA account/property with at least read access.

## 2. Set variables

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
export REGION="us-central1"
export REPO="analytics-mcp"
export SERVICE="analytics-mcp"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}:latest"
```

## 3. Enable required APIs

```bash
gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  analyticsadmin.googleapis.com \
  analyticsdata.googleapis.com
```

## 4. Create Artifact Registry repository

```bash
gcloud artifacts repositories create "${REPO}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Docker images for Analytics MCP"
```

If the repository already exists, this command can be skipped.

## 5. Build and push the image

```bash
gcloud builds submit --tag "${IMAGE}" .
```

## 6. Deploy to Cloud Run

Public service:

```bash
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080
```

Private service (recommended for production) uses `--no-allow-unauthenticated`
plus IAM-controlled access.

## 7. Verify health

```bash
SERVICE_URL="$(gcloud run services describe "${SERVICE}" --region "${REGION}" --format='value(status.url)')"
curl "${SERVICE_URL}/healthz"
```

Expected response:

```json
{"status":"ok"}
```

## 8. Connect from Gemini CLI as a remote MCP server

```bash
gemini mcp add --scope user --transport http analytics-mcp "${SERVICE_URL}/mcp"
gemini mcp list
```

Or set it directly in `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "analytics-mcp": {
      "httpUrl": "https://YOUR_CLOUD_RUN_URL/mcp"
    }
  }
}
```
