According to the supplied QuillCache 2.0 reference dated 2026-10-20, the default cache lifetime is **30 seconds**. The later third-party note says 60 seconds but cites the 1.0 announcement, so it does not establish a different 2.0 default. This conclusion is limited to the supplied packet. (Sections B, C, A.)

A lifetime of **zero disables cache writes**. It does not necessarily remove existing entries or prevent reads: existing entries may remain readable until their previously assigned lifetime expires. (Section B.)

The evidence **does not prove that 2.0 is twice as fast as 1.0**. The 1.0 announcement reports an internal median latency of 20 ms across 100 requests, without raw data or spread. The five-request local run has a calculated median of 10 ms, but its version and machine are unknown, and it used a warm cache. These are not controlled, comparable results. The third-party claim supplies no independent test. (Sections A, E, C.)

A valid comparison still needs identified 1.0 and 2.0 builds tested on the same hardware, workload, worker count, cache state, and stated lifetime settings, with sufficient repeated measurements and variability reported. Define “twice as fast”—for example, half the median latency or double throughput—and measure that metric directly. (Gaps in sections A, B, E.)
