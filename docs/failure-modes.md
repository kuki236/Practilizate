# Failure Modes — Practilizate

Written before parsing and quality logic. Each entry lists how the component can fail,
how the pipeline detects it, and what the user sees.

## Ingestion

| Failure | Detection | Behavior |
|---|---|---|
| `robots.txt` disallows a path | Fetch the policy before live ingestion | Abort live ingestion with a clear error |
| Filter form changes or career list is empty | Parsed career count is zero | Abort; fixtures remain usable |
| Career IDs change | Career names differ from the previous snapshot | Log the change; use IDs as published |
| Pagination markup changes | No cards or no pagination on page 1 | Stop and record a warning |
| Pagination loops forever | Same page URLs or same card URLs on consecutive pages | Stop at the repeated page |
| HTTP 429/5xx or timeout | Status code / exception in the fetcher | Retry with backoff, then fail the URL list |
| Rate limits ignored | Requests are serialized and spaced | Configurable delay; default 1 s |
| Cache corruption | Cached payload is not valid HTML | Ignore entry and refetch |
| Site serves mojibake | Decoding uses declared charset with UTF-8 fallback | Normalize text; quality rule flags leftovers |
| Duplicate card across career queries | URL keyed dedupe | Merge careers into one offer |
| Duplicate card within one query | URL keyed dedupe | One offer, one career link |
| Detail page missing | Listing remains with detail fields null | Quality report lists the gaps; no silent drop |
| JSON-LD missing or malformed | Structured parser returns nothing | Fall back to the listing card; flag the offer |
| Salary absent or non-numeric | `baseSalary` missing or text only | `salary_amount = null`, keep `salary_text` |
| Deadline absent | `validThrough` missing | `deadline_at = null`; quality rule 5 fails |
| Deadline before publication | Date comparison | Quality rule 6 fails; offer kept for audit |
| Published date invalid | Date parser rejects the value | `published_at = null`; quality rule 4 fails |
| Salary outlier | Bounds in settings (default 0–12 000 PEN) | Quality rule 8 fails; value kept |
| Missing company or location | Empty after normalization | Quality rules 9 and 10 fail |
| Unknown attendance | Not in the allowed set | Quality rule 12 fails; value kept |
| Skills not extracted | Detailed requirements but no lexicon match | Quality rule 15 fails |
| Personal data in a listing | Email/phone detection in requirements | Stripped from `requirements_text` before persistence |

## Normalization

| Failure | Detection | Behavior |
|---|---|---|
| Accents and casing vary | Shared `normalize_text` function | Canonical comparison keys |
| Company suffixes differ | Normalizer removes legal suffixes | One company dimension row |
| Location has district only | Location parser fills department from filters | Missing values remain null |
| Multi-career offer | More than one career query returns the URL | All careers linked |
| Duplicate title/company/deadline | Quality rule 14 | Flag both offers, keep both |
| Timezone differences | Dates stored as calendar dates | No timezone drift |
| Text contains control characters | Unicode normalization | Cleaned; quality rule 17 checks |

## Quality and load

| Failure | Detection | Behavior |
|---|---|---|
| Critical rule fails | Rule severity | Non-zero exit; run marked failed |
| Non-critical rule fails | Rule severity | Report warning; run continues |
| Duplicate `offer_id` | Primary key conflict | Transaction rollback; fail loudly |
| Database unreachable | Connection error | Non-zero exit with stage context |
| Partial load | Single transaction | Nothing is committed |
| Repeated load of the same run | Replace-in-transaction | Star schema reflects one snapshot |
| Invalid row in a dimension | Constraint violation | Rollback; report the offending row |

## Export

| Failure | Detection | Behavior |
|---|---|---|
| Missing columns | Explicit schema list | Fail before writing |
| Excel exceeds row limits | Row count guard | Fail with a clear message |
| Workbook repair warning | Openpyxl round-trip and ZIP check | E2E fails |
| Formula locale issues | ASCII formulas with English function names | Excel evaluates; labels stay Spanish |
| CSV encoding | UTF-8 with BOM for Excel compatibility | Round-trip check |
| Power BI dataset drift | CSV schema check in E2E | E2E fails |

## Power BI

| Failure | Detection | Behavior |
|---|---|---|
| CSV path missing | Report refresh error | README documents the path |
| Model TMDL invalid | MCP/TMDL review | Fix before commit |
| Language toggle broken | Two-language visual check | Release blocked |
| Contrast or alt text missing | Heuristics review | Release blocked |
| Report screenshot stale | Preview regenerated from the current CSV | Mismatch blocks release |

## Testing

The E2E suite uses synthetic fixtures that reproduce the medium-hard cases above.
Artifacts in `artifacts/e2e/` are the evidence. Fixtures are never edited to make a
test pass; the code or the documented source limitation changes instead.
