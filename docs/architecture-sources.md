# Architecture source and verification register

Original reference designs grounded in public Microsoft documentation. Documentation and asset provenance are verified; these systems are not deployed, certified, or cloud-tested.

Last successful public-source verification: **2026-10-27T09:25:58.627794+00:00**.

Verification means public HTTP 200 responses, expected evidence terms, manual review of the cited claims, and checked icon provenance. It does not mean implementation, deployment, regional entitlement or Microsoft certification.

A page may change after this review. Re-run the online verifier before relying on an activation-sensitive claim. Content hashes describe the fetched page at review time, not an immutable documentation release.

| ID | Official public source | Claim boundary |
|---|---|---|
| MS01 | [Azure architecture icons and permitted use](https://learn.microsoft.com/azure/architecture/icons/) | Official Azure SVG download, permitted architectural use, product labeling, and unchanged artwork. |
| MS02 | [Microsoft Fabric product, workload, and item icons](https://learn.microsoft.com/fabric/fundamentals/icons) | Official Fabric and Purview artwork, its Microsoft-owned distribution, and icon-use restrictions. |
| MS03 | [Baseline Microsoft Foundry chat reference architecture](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat) | Enterprise ingress, private connectivity, managed identity, agent tool/model flow, and dedicated agent-managed state. |
| MS04 | [Azure Container Apps overview](https://learn.microsoft.com/azure/container-apps/overview) | Consumption-style container API hosting, HTTPS ingress, and conditional scale-to-zero behavior; not a zero-cost guarantee. |
| MS05 | [External tenant email OTP sign-up and sign-in user flow](https://learn.microsoft.com/entra/external-id/customers/how-to-user-flow-sign-up-sign-in-customers) | External-tenant identity and email OTP configuration, not custom application session duration or daily quotas. |
| MS06 | [Design scalable and performant Azure tables](https://learn.microsoft.com/azure/storage/tables/table-storage-design) | Optimistic concurrency and atomic entity-group transactions within one table partition only. |
| MS07 | [What is ontology in Microsoft Fabric IQ? (preview)](https://learn.microsoft.com/fabric/iq/ontology/overview) | Entity types, properties, relationships, rules, source bindings, source-owned metrics, and optional graph execution; ontology is not a standalone data store/query engine. |
| MS08 | [Create relationship types in ontology (preview)](https://learn.microsoft.com/fabric/iq/ontology/how-to-create-relationship-types) | Origin/target relationship types, supported source bindings, Fabric capacity and tenant prerequisites. |
| MS09 | [Medallion architecture for Fabric with OneLake](https://learn.microsoft.com/fabric/onelake/onelake-medallion-lakehouse-architecture) | Raw, enriched, and curated data layers, separated lakehouses/warehouses, and Delta-oriented refinement. |
| MS10 | [Data quality in Microsoft Purview Unified Catalog](https://learn.microsoft.com/purview/unified-catalog-data-quality) | Profiling, configured rules, scans, scores, six quality dimensions, managed identity, permissions and regional prerequisites. |
| MS11 | [Create data quality rules](https://learn.microsoft.com/purview/unified-catalog-data-quality-rules) | Specific rule semantics, null-handling caveats, lookup checks, and freshness based on asset modification metadata. |
| MS12 | [Sources and file formats supported for Purview data quality](https://learn.microsoft.com/purview/unified-catalog-data-quality-supported-sources-file-formats) | Fabric lakehouse and supported file-format scanning; support remains subject to current connection, region, and source restrictions. |
| MS13 | [Data quality in Fabric materialized lake views](https://learn.microsoft.com/fabric/data-engineering/materialized-lake-views/data-quality) | Explicit transformation-time quality enforcement, including FAIL/DROP semantics; these differ from Purview assessment scores. |
| MS14 | [Plan and manage costs for Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/manage-costs) | Usage-based AI costs and potentially idle fine-tuned hosting charges; diagrams do not imply those services fit the lean budget. |

## Reproduce

```powershell
.\.venv\Scripts\python.exe scripts\build_architecture_atlas.py --verify-sources
.\.venv\Scripts\python.exe scripts\build_architecture_atlas.py --check
```

The first command performs public HTTP requests and rebuilds artifacts only after all checks pass. The second is deterministic and offline. Review source meaning manually after product changes; term matching is not a substitute for architectural review.

See [icon terms and provenance](assets/icons/NOTICE.md) and [machine-readable verification](assets/architecture-verification.json).
