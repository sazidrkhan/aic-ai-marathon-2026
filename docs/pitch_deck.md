# ReconMate Pitch Deck

## Slide 1: Title
**ReconMate – Global Treasury Reconciliation Agent**

AI Marathon 2026 | Problem Statement 3: The Global Treasury Agent

Team: [Your Team Name]

---

## Slide 2: The Problem
**SMEs Struggle with Cross-Border Reconciliation**

- Receive RM42.50 in bank, but invoice was for USD10
- Manual matching requires FX calculation, fee accounting, logging
- Error-prone, time-consuming, and expensive for small businesses
- **Pain**: SMEs lack dedicated treasury teams but still deal with multi-currency transactions

---

## Slide 3: The Solution
**ReconMate – An Agentic AI Reconciliation System**

- **OCR**: Extracts structured data from payment proof images (third-party receipts, invoices)
- **FX + Fee Tools**: Calculates exact exchange rates and bank fees for the transaction date
- **Matching Engine**: Matches payment proofs against bank statement rows with confidence scores
- **Agent Documents**: Auto-generates Reconciliation Reports and Discrepancy Summaries via Chutes LLM
- **Architecture**: Deterministic tools + LLM for explanations (not calculations)

---

## Slide 4: How It Works (Agent Framework Diagram)

```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│   Payment Proof │   Bank Statement│   FX/Fee Tools  │  LLM Agent      │
│   (Image/PDF)   │   (CSV/JSON)    │   (Deterministic)│  (Chutes-powered)│
└────────┬────────┘└────────┬────────┘└────────┬────────┘└────────┬────────┘
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ReconMate Agent Pipeline                        │
│  1. PaddleOCR → Extract text from payment proof images                  │
│  2. Parser → Structured data (amount, currency, reference, date)      │
│  3. Matcher → Reference + amount + date + FX/fee tolerance matching   │
│  4. Agent Documents → Chutes LLM generates finance-friendly reports     │
│  5. Output → Reconciliation Report + Discrepancy Summary               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Slide 5: Key Innovation
**Finance-Safe Agent Design**

- **Deterministic tools** calculate FX, fees, match status, confidence
- **LLM only explains** structured facts — never invents or recalculates
- **Template fallback** ensures demos never fail even if LLM is unavailable
- **Full agent trace** visible to satisfy judging criteria

---

## Slide 6: Tech Stack
- **Backend**: Python, FastAPI
- **LLM**: Chutes.ai (Hermes-compatible)
- **OCR**: PaddleOCR
- **Frontend**: HTML/JS (Lovable AI for React version)
- **Deployment**: Uvicorn + local runs

---

## Slide 7: Demo Results
**Template Fallback (No API key)**
- ✅ Reconciliation Report generated
- ✅ Discrepancy Summary generated
- ✅ Agent trace with 4 steps visible
- ✅ Published at `/api/reconcile`

**Live Chutes (With API key)**
- ✅ Same output structure, richer natural-language explanations
- ⚠️ Rate-limited on free tier (429 fallback handled gracefully)

---

## Slide 8: Future Potential
- Real-time FX API integration (exchangerate-api.com)
- Multi-bank statement formats (SWIFT, SEPA, domestic)
- Email / Slack notification for discrepancies
- PDF export of reconciliation reports
- Cloud deployment (Docker / AWS Lambda)

---

## Slide 9: Team
- **Backend / AI Agent**: Your Name
- **Frontend**: Syafieqah (Lovable AI)
- **Problem**: Track 3 – The Global Treasury Agent

---

## Slide 10: Thank You
**ReconMate – Because SMEs deserve enterprise-grade reconciliation.**

