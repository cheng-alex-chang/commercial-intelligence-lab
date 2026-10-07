# Commercial intelligence at TTD's financial scale

Updated October 7, 2026. The default lab now uses large commercial volumes and a wider account/campaign population. Actual processing performance is measured separately from the business quantities represented in each record.

## Public references

TTD reported 2025 gross spend of **$13.4 billion** and revenue of approximately **$2.9 billion**. Gross spend and revenue are distinct. Dividing annual gross spend by 365 gives a financial scale reference of approximately **$36.7 million/day**, rather than an estimate of any actual 2026 day. [TTD's 2025 financial results](https://investors.thetradedesk.com/news-and-events/news/news-details/2026/The-Trade-Desk-Reports-Fourth-Quarter-and-Fiscal-Year-2025-Financial-Results/default.aspx).

TTD's August 27, 2026 Kokai Zuma announcement describes analysis of **more than 20 million ad impressions per second**. That is a platform analysis measure, distinct from the paid impressions in this lab. [TTD's platform announcement](https://investors.thetradedesk.com/news-and-events/news/news-details/2026/The-Trade-Desk-Introduces-Kokai-Zuma-the-Latest-Release-of-Kokai/default.aspx).

## Implemented default

| Quantity | Synthetic commercial profile |
| --- | --- |
| Account population | 1,000 fictional accounts |
| Campaign population | 5,000 campaigns; five per account |
| History | 56 business dates ending August 31, 2026 |
| Normal-day spend calibration | $36,712,328.76 before daily variation and planted scenarios |
| Accepted delivery aggregates | 279,960 campaign × date × channel records |
| Account-day view | 56,000 rows |
| Observed spend over the fixture history | $2,047,582,442.77, seed 42 |
| Implied paid impressions over the fixture history | 338,991,332,198, seed 42 |
| Source file count | 170 baseline JSON files |

Account and campaign counts, account-size distribution, owner/agency assignment, channel mix, daily variation, and prices are synthetic assumptions. They are not estimates of TTD's actual customer population or customer economics. The dates are fictional analytical periods. Seasonality, real client mix, and actual platform pricing are not inferred from the public annual average.

`spend_usd` is a financially calibrated synthetic spend proxy, not a reconstruction of TTD's accounting gross spend. Effective CPMs are explicit assumptions: display $4, CTV $25, audio $12. They derive paid impression counts while keeping spend and impressions numerically consistent. This does not imply a reported TTD CPM or that all platform-analyzed inventory is purchased.

## Scenarios now use enterprise amounts

| Account | Prior seven-day spend | Current seven-day spend | Current planned spend |
| --- | --- | --- | --- |
| Atlas | $2,800,000 | $1,050,000 | $3,500,000 |
| Beacon | $2,800,000 | $0 | $0 |
| Harbor | $2,800,000 | Unknown: final delivery file missing | $3,500,000 |
| Maple | $2,800,000 | $0 observed | $3,500,000 |

Atlas's correction changes final-day account spend from $150,000 to $400,000, across five campaign rows. Harbor's late file recovers $400,000. Missing data remains unknown even when the dollar quantities are large.

## Local processing and larger exercises

The default records are aggregates that commercial analytics could consume. A record can represent millions of paid impressions without containing millions of impression-event rows. This project does not claim to handle TTD's live analysis throughput. Future event-level exercises should use a bounded event sample or load test, with raw-event counts and measured rows/second reported explicitly.

The generator supports changing `--accounts`, `--campaigns-per-account`, and `--days`. Increasing account/campaign counts divides the calibrated financial target across more entities; it does not multiply spend. Increasing days expands history. The `unit` profile contains 10 accounts, one campaign each, and the same enterprise scenario values for quick tests.

Generated `scale_manifest.json` records actual row counts, amounts, seed, assumptions, and the financial source. Runtime measurements and integration evidence are recorded in [VERIFICATION.md](../docs/VERIFICATION.md).

The original small lab database `ttd_lab` is retained. The new default is `ttd_lab_scale`, avoiding conflicting source versions or removal of your original evidence.
