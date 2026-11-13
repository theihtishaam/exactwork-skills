QuillCache 2.0 defaults to a **30-second cache lifetime**, according to the version-specific reference (§B). The 60-second default belongs to 1.0 (§A); the later third-party note repeats that older value without independent support (§C).

Setting the lifetime to **zero disables cache writes**. It does not necessarily make existing entries unreadable: they may remain readable until their previously assigned lifetime expires (§B).

The packet **does not prove that 2.0 is twice as fast as 1.0**. The 1.0 announcement reports a 20 ms median across 100 local requests, but supplies neither raw data nor variability (§A). The local run has a 10 ms median across five warm-cache requests, yet its version and machine were not recorded, and it explicitly is not a controlled comparison (§E). Those medians alone cannot establish a version-related speedup. The third-party claim provides no independent test (§C).

A controlled comparison still needs both identified versions on the same hardware, configuration, worker count, workload, and cache conditions—including matched lifetimes—with repeated, adequately sized runs and raw latency distributions. A claim about throughput would also require matched throughput measurements.
