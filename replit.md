# Ransomware Defense SOC

## Run on Replit

The preview is served by the single `Start application` workflow:

```bash
python dashboard.py
```

It listens on port 5000 and serves the Flask dashboard at `/`. The dashboard reads existing events from `logs/events.jsonl`; it does not start the system monitors or detection pipeline automatically.