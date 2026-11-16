# Run comparability notes

Recorded 2026-11-16 (America/New_York).

- Source base commit: `ad9151925c4d6e49c8db7b7bc5c520cdc18e9740`.
  The implementation commit containing these notes also captures the previously
  uncommitted harness behavior used for the November runs. No new search-loop
  decisions were added; the new harness edits only save response token counts.
- Ollama client and historical server version: `0.40.15`.
- Model: `qwen2.5-coder:7b`; local manifest ID
  `4aaba1ee422af93aad53ecbdfc8a159770cf254a9950b7a4304cf9ee3555ef31`
  (short ID `4aaba1ee422a`). `ollama list` could not be queried because the server
  was stopped; the ID was calculated from its on-disk manifest instead.
- Temperature: `0.8`; context window (`num_ctx`): `4096`.
  Both are confirmed in historical per-request server logs and are now explicit
  request options. No seed is set. Historical random seeds were not recorded.
- All 30 saved prompts fit the context window; corresponding server requests
  recorded `truncated = 0`. New responses save `prompt_eval_count` and `eval_count`
  in an attempt-specific `_counts.json` beside the prompt and reply.
- Full and metrics_only retain the same template, model settings, starting state,
  and search rules; only warnings/history blocks differ between conditions.

| Existing run | Decision | Reason |
| --- | --- | --- |
| 20261112_1425_full | counted | Same supported working-code version and confirmed settings; no prompt truncation. Best valid latency remains 16,395 cycles. Attempt 10 qualification below. |
| 20261113_1626_full | counted | Same supported working-code version and confirmed settings; no prompt truncation. Best valid latency 16,395 cycles. Wrong-result and duplicate attempts remain part of the ten-attempt budget. |
| 20261113_1721_metrics_only | counted | Same supported working-code version and confirmed settings; no prompt truncation. Best valid latency 1,361 cycles. Wrong-result attempt remains part of the ten-attempt budget. |

## Attempt 10 synthesis retry

`20261112_1425_full`, attempt 10, passed CSim originally, but its original synthesis
log ended mid-process without a completed result. Its saved kernel was re-run on
2026-11-16, without any LLM call, using the unchanged Makefile/Tcl flow:

```bash
export PATH="$PATH:/c/Program Files (x86)/GnuWin32/bin:/c/AMDDesignTools/2025.2/Vitis/bin"
make bench KERNEL=gemm VARIANT=20261112_1425_full_iter10
```

The harness label is `gemm_20261112_1425_full_iter10`. The retry failed (make exit
code 2): Vitis resolved the component path to
`C:/Users/wwa228/hls-llm-study/build/gemm_gemm_20261112_1425_full_iter10` and failed
with permission denied while trying to create that directory. This was a setup
failure before CSim/synthesis, not evidence of an invalid kernel. Per the study
owner's instruction it is recorded as a synthesis failure, with this qualification.
No metrics row was appended and the attempt is not accepted. The current best
remains 16,395 cycles; no completed measurements exist to test against the fit
limits (53,200 LUT, 106,400 FF, 220 DSP, 280 BRAM_18K, 10 ns).

The retry transcript is `results/20261112_1425_full_iter10_resynthesis.log`.
Counting this run is explicitly requested by the study owner despite the
unresolved original synthesis outcome. The batch has not been started.
