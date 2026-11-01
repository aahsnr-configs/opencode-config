# Life-sciences integration: initial foundation

This is an incomplete foundation for the attached research report, not the report's claimed full deliverable. The report itself did not include source code, benchmark data, or logs. Its numerical validation claims have not been reproduced. Use only public, non-sensitive queries. No component is intended for clinical decisions.

## Use

Run `./install.sh --dry-run`, review, and follow the existing installer instructions to install the new `/life-science` command and skill with the base configuration. OpenChamber uses the same OpenCode setup; availability in its UI has not been tested here. The script below remains in the repository; the installer does not copy it.

```sh
python3 life-sciences/lookup.py alphafold P00520
python3 life-sciences/lookup.py literature 'TP53 AND cancer' --limit 5
```

These commands send their arguments to external public services. Output contains the upstream JSON, request URL, and retrieval time; redirect it to a file if a record is needed. Network access is required. Avoid sensitive material. AlphaFold returns precomputed predictions, not a new fold, and model confidence is not experimental confirmation.

## Coverage and evidence

| Capability | Status |
| --- | --- |
| Europe PMC literature and AlphaFold DB metadata | Implemented; offline mocked tests only, live requests not verified in this environment |
| OpenCode command and skill | Added; installer behavior tested; OpenCode and OpenChamber runtime discovery not tested |
| BLAST, SAMtools, STAR adapters; MCP server | Not implemented |
| Nextflow pipelines, containers, execution manager, full tool registry | Not implemented |
| GIAB, ENCODE, spike-in, docking and pathway benchmarks | Not run; report's results unverified |
| Protected clinical data | Not supported |

Do not infer dataset quality or biological validity from an HTTP success. A complete implementation still needs actual pinned workflows, controlled inputs, external dependencies, logs, reproducible reference datasets, and independent scientific validation. There is no generic shell adapter or service listening on a network port.

## Sources

- [OpenCode V2 configuration](https://opencode.ai/v2/docs/config/) and [MCP](https://opencode.ai/v2/docs/mcp-servers/).
- [AlphaFold DB API](https://alphafold.ebi.ac.uk/api-docs), [Europe PMC REST API](https://europepmc.org/RestfulWebService).
- [nf-core/rnaseq documentation](https://nf-co.re/rnaseq/latest/docs/usage/): candidate upstream workflow, not installed or tested here. Pin a release and follow its own documentation before using it.
