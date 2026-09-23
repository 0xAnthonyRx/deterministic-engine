# Deterministic Extraction Engine

An enterprise-grade data extraction service that enforces strict schemas, cross-field arithmetic validation, and automated error-recovery on unstructured business text using **Pydantic v2**, **Instructor**, and **LiteLLM**.

---

## The Problem
Large Language Models are probabilistic text generators. When integrated into accounting, ERP, or inventory backends, hallucinated keys, markdown formatting, or subtle mathematical contradictions silently corrupt transactional records.

## Architecture & Defense Layers
Raw Unstructured Text (Invoice/Email)
│
▼
LLM (LiteLLM / Groq)
│
▼
Instructor Interception Layer
│
▼
Pydantic v2 Schema
├─► @field_validator: ISO-4217 Currency Normalization
├─► @model_validator: Line Item Math (qty * unit_price == total)
└─► @model_validator: Grand Total Sum Integrity
│
├─► [PASS] ──► Validated JSON / Typed Model
│
└─► [FAIL] ──► Self-Healing Retry Loop
Validation traceback fed back to LLM
for targeted recalculation (Max 3 retries)

## Features
- **Deterministic Type Contracts:** Enforces strict ISO dates, standard 3-letter currency codes, and positive quantities.
- **Cross-Field Mathematical Integrity:** Catches discrepancies between vendor-stated totals and actual line-item calculations.
- **Automated Healing:** Feeds Pydantic validation tracebacks directly back to the model context window to force correction before returning.
- **Multi-Model Abstraction:** Operates through LiteLLM for zero-downtime provider fallback routing.

## Verification & Test Suite

The pipeline includes an automated test harness covering standard multi-item invoices, contradictory vendor calculations, and non-commercial inputs.

```bash
# Run test suite
pytest -v

test_extractor.py::test_standard_invoice_extraction PASSED      [ 33%]
test_extractor.py::test_contradictory_math_self_heals PASSED     [ 66%]
test_extractor.py::test_non_transactional_text_handling PASSED   [100%]
============================== 3 passed in 17.64s ==============================
```bash
