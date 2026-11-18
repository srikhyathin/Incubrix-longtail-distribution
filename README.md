# IncuBrix Long-Tail Distribution Service

A containerized, high-reliability microservice built to the **IncuBrix Connector Contract** and **Integration Standard**, enabling automated publishing across Discourse, Lemmy, Dev.to, Ghost, HMAC webhooks, and assisted communities.

## Architecture Diagram
[ FastAPI REST / Connector API ] ---> [ Posting-Rules Engine ] ---> [ Connector Registry (6 Core) ]
                                            |
                                    [ Certification Harness ] ---> [ Sandbox / JSON Evidence ]

## Setup & Running in Under 10 Commands
1. python -m venv .venv
2. .venv\Scripts\Activate.ps1
3. python -m pip install --upgrade pip
4. pip install -r requirements.txt
5. Copy .env.example to .env
6. python -m uvicorn app.main:app --reload

## Running Tests & Batch Runner
* Run unit and certification tests: `python -m pytest -v`
* Run batch test runner: `python tests/batch_runner.py`

## Error Codes
* `DEST_SPEC_VIOLATION`: Format limits or unsupported fields broken.
* `DEST_RULE_FREQUENCY_CAP`: Frequency cap reached; reschedule.
* `CONNECTION_AUTH_EXPIRED`: Token expired or revoked.
* `PLATFORM_RATE_LIMIT`: Rate limited; back off using reset time.