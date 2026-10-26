# VigiloForge report email CTA

The crop imaging panel displays an **optional** email form after an image is analyzed. The on-screen result is not gated behind email. Email delivery sends only the four numerical observations (no raw image).

The endpoint is `POST /reports/email`. It requires an authenticated private workspace session and explicit `consent_to_email: true`; unauthenticated users cannot send mail. A one-email-per-workspace-per-UTC-day SQLite limit is applied to help control abuse. This is **not** the scan quota and does not unlock 10 free scans.

Configure the following **server-only** environment variables (never NEXT_PUBLIC and never commit real secrets):

```dotenv
VIGILO_SMTP_HOST=
VIGILO_SMTP_PORT=465
VIGILO_SMTP_USER=
VIGILO_SMTP_PASSWORD=
VIGILO_SMTP_FROM=
```

SMTP must support implicit TLS on port 465. If unset, the endpoint returns HTTP 503 and the interface displays an error rather than claiming an email was sent. The HTTP response confirms submission to SMTP, not inbox delivery. A failed SMTP send consumes that day's slot in the prototype until a safe retry workflow is implemented.

## Local testing

1. Start FastAPI using `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`.
2. Start Next.js inside `frontend` using `npm.cmd run dev`.
3. Create or sign in to a private workspace on `/login`.
4. Analyze a leaf photograph on the homepage.
5. Enter an email address and explicitly check the consent box.
6. Select **Email my crop results**. If SMTP is not configured, you should receive an honest 503.

## Not yet enabled

- Anonymous introductory one-scan quota
- Email/password authentication and verified account signup
- Unlocked 10 free scans per day after email verification
- Paid 100/day and Platinum entitlements, upgraded LLM
- Card-only checkout and subscription renewal webhooks

These require a durable identity store, verification emails, server-enforced analysis quotas, and a payment provider. Do not market the proposed limits as active until shipped and tested.
