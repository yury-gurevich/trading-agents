# Points of no return — system-wide registry

Every **irreversible** operational step, rolled up from each charter's `OPS-PNR` section.
Before executing any row here, `ta` MUST: (1) show blast radius, (2) snapshot state,
(3) require an interactive confirmation. If a step can be undone, it is NOT here — it has a
Rollback instead.

| PNR ID | Subsystem | Irreversible step | Why | Guard |
| --- | --- | --- | --- | --- |
| PNR-ID-01 | identity-secrets | Delete Key Vault w/ purge-protection | name locked 90d; secrets gone | confirm + export inventory |
| PNR-ID-02 | identity-secrets | Delete the OIDC app | breaks all CI deploy (outage, re-creatable) | confirm |
| PNR-GR-01 | graph-store | Delete an Aura/Neo4j instance | data gone unless backed up | confirm + snapshot/export first |
| PNR-GR-02 | graph-store | Region migration cutover | old region decommissioned post-cutover | confirm + verified restore in target |
| PNR-RG-01 | region-residency | Delete a resource group | all contained resources gone | confirm + inventory + verify moved |
| PNR-FL-01 | fleet-compute | Delete the Container Apps environment | env FQDN/domain regenerates; all apps drop | confirm |

> This registry is the teeth behind the "don't go blind into a costly, unrecoverable move"
> principle. Adding a destructive action anywhere → add its row here in the same change.
