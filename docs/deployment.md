# Room Matcher AI Deployment Guide

This runbook documents how university and partner operations teams promote new
versions of the Room Matcher AI service to Google Cloud Run using Cloud Build.
It covers the automated trigger, secrets and configuration, rollout checks, and
rollback guidance.

## 1. Prerequisites

- Google Cloud project with the `room-matcher-ai` artifact repository and Cloud
  Run service provisioned.
- Cloud Build service account granted the following roles:
  - `roles/run.admin`
  - `roles/secretmanager.secretAccessor`
  - `roles/artifactregistry.writer`
- Secret Manager entries populated:
  - `firestore-service-account` – JSON service account key with access to
    Firestore.
  - `faiss-availability` – string flag (`true`/`false`) toggling semantic FAISS
    retrieval.
- Optional: configure a Cloud Build substitution `_MODE` when running manual
  builds to override the default deployment mode (`online`).

## 2. Cloud Build Trigger

1. Push the desired commit to the configured Git branch (typically `main`).
2. Cloud Build executes `cloudbuild.yaml` which:
   - Builds and pushes the container image to
     `asia-south1-docker.pkg.dev/<PROJECT_ID>/rm-repo/room-matcher-ai` tagged
     with the commit SHA.
   - Deploys the new revision to Cloud Run with
     `MODE`, `FIRESTORE_ENABLED`, `CACHE_TTL_SEC`, and `ENABLE_STARTUP_WARMUP`
     environment variables, and mounts `FIRESTORE_CREDENTIALS` and
     `FAISS_ENABLED` from Secret Manager.
   - Enables proactive health checks by configuring the `/healthz` endpoint and
     keeps one instance warm (`--min-instances=1`).

### Manual trigger

```bash
gcloud builds submit --config cloudbuild.yaml --substitutions=_MODE=degraded
```

## 3. Post-deploy Verification

1. Confirm the service revision is ready:
   ```bash
   gcloud run services describe room-matcher-ai \
     --region=asia-south1 --format='value(status.latestReadyRevisionName)'
   ```
2. Hit the health endpoint which now exposes cache statistics and request
   metrics:
   ```bash
   curl https://<service-url>/healthz | jq
   ```
   Check for `status: ok`, `faiss_enabled`, cache counts, and `metrics` totals.
3. Warm the caches to ensure low-latency responses using the provided helper:
   ```bash
   python scripts/warm_cache.py --url https://<service-url>
   ```
   The script POSTs to `/__internal/warmup` which triggers Firestore/JSON cache
   hydration and optional FAISS loading. Successful runs emit structured JSON
   summarising cache counts and warmup duration.
4. Tail structured logs and ensure request metrics increment when hitting test
   endpoints:
   ```bash
   gcloud logs tail --project <PROJECT_ID> --format=json --log-filter='resource.type="cloud_run_revision"'
   ```

## 4. Rollback Procedure

If issues are detected:

1. Identify the last known-good revision:
   ```bash
   gcloud run revisions list --service room-matcher-ai --region=asia-south1
   ```
2. Roll back by redeploying the prior revision:
   ```bash
   gcloud run services update-traffic room-matcher-ai \
     --region=asia-south1 --to-revisions <REVISION_NAME>=100
   ```
3. Re-run the verification checklist (health check, warmup script, log tailing)
   to confirm stability.

Document any incidents and configuration tweaks in the shared operations log so
future rollouts incorporate the learnings.
