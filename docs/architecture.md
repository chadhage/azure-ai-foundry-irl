# Azure Foundry IRL: showcase architecture

## Status and scope

This is the proposed architecture, not a deployment report. The local microsite
and read-only catalog API work. Authentication, durable quotas, live AI calls,
infrastructure, and publishing are not implemented or deployed.

The [reference architecture atlas](reference-architectures.md) now provides
topology and sequence diagrams with official Microsoft icons. The
[ontology and data-quality guide](ontology-and-data-quality.md) documents the
connected Fabric/Purview patterns and synthetic business model. See the
[dated source register](architecture-sources.md) for verified public citations
and precise claim boundaries. These diagrams do not represent deployed resources
or expand the lean budget to include every illustrated service.

The showcase serves executive, architect, developer, and CSA journeys through a
capability expo rather than a single industry story. Its eventual catalog covers
Foundry, connected Azure services, public previews, and officially published
gated capabilities. Product availability and this demo's execution status must
always be separate labels.

Only original synthetic demonstration data is published. Real registration
identities are necessarily personal data and require a privacy notice, limited
retention, restricted access, and exclusion from public datasets and traces.

## Hosting and service boundaries

| Layer | Proposed implementation | Boundary |
|---|---|---|
| Public microsite | HTML, CSS, JavaScript on GitHub Pages | Public explanations and code; no provider credentials or anonymous AI execution |
| Visitor identity | Microsoft Entra External ID external tenant, email one-time passcode user flow | Verified identity is not automatic approval to run demos |
| Demo API | Python/FastAPI on Azure Container Apps Consumption | HTTPS, explicit origins, validated access tokens, approved visitors, and server-side admission control |
| Durable state | Standard LRS Storage Tables | Approved identities, session starts, absolute expiry, atomic counters, and spending reservations |
| Synthetic assets | Repository downloads and private Blob Storage when needed | No real customer documents, arbitrary remote URLs, or production enterprise actions |
| AI platform | Foundry resource and project; individually activated consumption deployments | Actual SDK execution only after model, quota, pricing, and access checks |
| Operations | Managed identity, ACR Basic, Standard Key Vault, Application Insights and Log Analytics | Scoped permissions, sanitized telemetry, bounded retention, and explicit teardown |

The lean API profile proposes one worker, 0.25 vCPU, 0.5 GiB, zero minimum
replicas, and one maximum replica. Cold starts are an intentional cost tradeoff.
Security accounting must remain durable and race-safe even with one worker or
replica; process-local counters are not an acceptable shortcut.

Do not silently enable dedicated workload profiles, Container Apps private
endpoints, or planned-maintenance features. These can introduce management fees
even when application compute uses Consumption. If governance requires them,
revisit the architecture and budget before provisioning.

## Visitor access contract

The following is proposed behavior to implement and test, not current behavior:

1. A visitor registers and authenticates using Entra-managed email OTP. Do not
   implement a homegrown OTP sender, password store, or token issuer.
2. The API validates the token's signature, issuer, audience, lifetime, and
   required permissions. A separate approved-visitor record authorizes access.
3. An explicit successful session start consumes one of three starts for that
   approved identity in a **UTC calendar day**. This day boundary is a proposed
   default requiring architecture approval.
4. An authorized application session expires **900 seconds after creation**.
   Activity, refresh tokens, page reloads, or a new identity token do not extend it.
5. Session creation and counters use conditional writes/transactions, with
   idempotent retries. Concurrent requests must not create a fourth daily session.
6. Every paid action validates the session and reserves a bounded usage allowance
   before contacting a provider. Unknown prices or unavailable accounting fail
   closed. Identity and session limits do not replace a global usage allowance.
7. Streaming, voice connections, tool loops, and background operations respect the
   remaining session deadline. A browser countdown alone is not enforcement.
8. Registration, OTP abuse controls, request size, concurrency, tokens, uploads,
   tool permissions, and per-demo duration receive separate limits. Model tools
   must not become arbitrary code execution, URL fetchers, or Azure admin proxies.
9. Expired, unapproved, or exhausted sessions receive explicit actionable errors.
   Never substitute canned answers while claiming a live model succeeded.

Three sessions per identity is not proof of three sessions per human. Known-user
approval and abuse monitoring address that limitation. CORS is not authorization,
and a GitHub Pages repository path is not a distinct web origin.

## Coverage and evidence contract

Each eventual capability entry should identify:

- Whether it is Foundry-native, a connected Azure service, or reference-only.
- Its official availability state and regional/model/subscription prerequisites.
- Whether this repository's implementation is planned, deployed, disabled,
  awaiting approval, or unavailable.
- Official citations, the date reviewed, and any access/preview limitations.
- Original explanation, executable sample, synthetic inputs, expected output
  contract, evaluation criteria, deployment profile, cost notes, and cleanup.
- A smoke-test result before any claim that a deployed demo is working.

Do not invent roadmap dates or claim access to gated features. A documented
walkthrough, synthetic illustration, or future replay must be labeled as such,
not presented as a live result.

## Cost model

Retail meters were retrieved on 2026-10-27 for the **eastus2 candidate region**.
These are illustrative incremental showcase costs, not the existing
subscription's total bill, a quote, or a hard spending cap.

| Priced item | Explicit monthly assumption | Estimated USD |
|---|---|---:|
| Container Apps Consumption | 30 active hours at 0.25 vCPU/0.5 GiB; 100,000 requests | 0.85 |
| ACR Basic | 30 days at USD 0.1666/day | 5.00 |
| Storage | 1 GB Hot LRS Blob, 1 GB LRS Table, 1 million Table operations | 0.10 |
| Standard Key Vault | 10,000 operations | 0.03 |
| Log Analytics | 1.5 GB ingestion at USD 2.76/GB | 4.14 |
| **Priced infrastructure subtotal** | Does not assume remaining shared free grants | **10.12** |

**AI inference, agent tools, retrieval/vector storage, speech/media processing,
fine-tuning, fine-tuned hosting, and optional services are excluded from that
subtotal. They are not free.** Model-specific prices and capacity must be verified
before activation. Fine-tuned deployments can incur hourly hosting charges even
while unused.

A proposed USD 100 envelope reserves USD 15 for lean infrastructure, USD 60 for
application-admitted AI usage, and USD 25 for overhead/contingency. Actual billing
can exceed an application estimate: retries, provider metering, image builds,
egress, policy-added services, taxes, and traffic must be considered. Azure budget
alerts do not stop spending. Neither quota settings nor delayed billing telemetry
are substitutes for fail-closed application admission control.

Entra External ID's core offer is free for the first 50,000 monthly active users,
subject to the applicable combined usage and subscription linkage. Do not assume
unused free capacity or credits. Premium identity add-ons and SMS are not part of
this proposal.

## Phased delivery

1. **Local foundation: verified.** Public-content prototype, nine synthetic
   concepts, metadata API, 34 passing tests, and browser validation. Not published.
2. **Secure live core: proposed.** Identity/approval, durable 15-minute sessions,
   three starts/day, cost reservations, then a small real model/agent/grounding
   lineup with structured output, citations, and modest evaluation workloads.
3. **Breadth expansion: proposed.** Vision, voice, media, enterprise integrations,
   and advanced agent scenarios, with individual cost/capacity gates.
   Fine-tuning and high-cost provisioning remain administrator-controlled.
4. **Reusable showcase release: proposed.** Source-verified catalog, articles,
   diagrams, reference architectures, wiki content, synthetic datasets, regression
   harnesses, Bicep modules, YAML CI/CD, one-command lean deployment, and teardown.

Maximum catalog breadth does not mean every service runs continuously within
USD 100. Paid AI Search, GPUs, provisioned throughput, training, premium gateways,
and idle fine-tuned hosting are not silently included in the lean baseline.

## Deployment gates still open

- Confirm the subscription, resource group, candidate region, architecture, and
  estimates before generating infrastructure; obtain separate deployment approval.
- Capacity checks covered eastus2 and westus3. Container Apps, Storage, and Foundry
  account capacity had headroom; ACR, Key Vault, and monitoring quotas remain
  unverified. Neither region is claimed fully validated.
- Verify model-specific TPM/RPM capacity, lifecycle, price, feature compatibility,
  and regional processing behavior before enabling each live module.
- Create or configure an Entra external tenant and its app registrations/user
  flow with appropriate administrative approval. No tenant migration is proposed.
- Respect inherited governance policies. The inspected deny initiative blocks
  provisioned OpenAI capacity; this proposal uses consumption, not PTUs or policy
  exemptions. Effective policy and deployment validation remain mandatory.
- Validate the Linux package/runtime, lock a tested dependency set, and resolve
  the current upstream TestClient/httpx deprecation before release promotion.

## Official sources

- [Foundry costs and billing models](https://learn.microsoft.com/azure/foundry/concepts/manage-costs)
- [Container Apps billing and conditional management fees](https://learn.microsoft.com/azure/container-apps/billing)
- [External ID email OTP user flows and prerequisites](https://learn.microsoft.com/entra/external-id/customers/how-to-user-flow-sign-up-sign-in-customers)
- [External ID billing and subscription linkage](https://learn.microsoft.com/entra/external-id/external-identities-pricing)
- [External ID core-offer pricing](https://azure.microsoft.com/en-us/pricing/details/microsoft-entra-external-id/)
- [Azure Retail Prices API](https://prices.azure.com/api/retail/prices)
