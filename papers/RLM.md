# Recursive Language Models

By Alex L. Zhang

## Overview

The paper introduces **Recursive Language Models (RLMs)**, an inference strategy enabling language models to decompose and recursively interact with unbounded input context through REPL environments.

## Key Concept

RLMs allow models to "recursively call themselves or other LLMs" before providing final answers. The approach enables processing of essentially unbounded context and output lengths while mitigating context degradation.

## Core Design

The implementation uses a Python REPL environment storing the user's prompt as a variable. Models can:
- Query subsets of context programmatically
- Launch recursive LM calls over chunks
- Peek at, partition, grep, and transform data
- Return final answers via `FINAL()` or `FINAL_VAR()` tags

## Main Benefits

1. Root LM context window remains unclogged—it never directly sees entire context
2. Flexibility to view context subsets and naively recurse over chunks
3. Support for any modality loadable into memory with full transformation control

## Research Results

### OOLONG Benchmark (132K-263K tokens)
- **RLM(GPT-5-mini) outperforms GPT-5 by >33%** on long-context reasoning tasks
- Maintains comparable API costs per query
- Performance degradation occurs primarily for counting problems at larger scales

### BrowseComp-Plus (Up to 1000 documents)
- RLM achieves perfect performance at 1000-document scale
- Only iterative methods maintain reasonable performance with 100+ documents
- RLM(GPT-5) sustains accuracy while handling 10M+ tokens

## Emergent Strategies

Models develop interpretable interaction patterns:

1. **Peeking** - Examining initial context structure
2. **Grepping** - Using regex/keywords to narrow search space
3. **Partition + Map** - Chunking context for semantic mapping via recursive calls
4. **Summarization** - Condensing information for outer LM decision-making
5. **Long-input, long-output** - One-shot programmatic task execution (diffs, git logs)

## Limitations

- Implementation lacks optimization for speed—recursive calls are blocking
- No prefix caching utilized
- No strong guarantees on API cost or runtime control
- Performance varies significantly based on partition strategy

## Relationship to Existing Work

RLMs differ from agents by treating decomposition contextually rather than problem-focused. Unlike summarization-based approaches in code assistants (Cursor, Claude Code), RLMs delegate decomposition decisions entirely to the model itself.

## Future Directions

- Training models explicitly for recursive reasoning
- Applying fixed-format principles (CoT, ReAct, instruction-tuning) to RLMs
- Performance improvements correlating directly with base model capabilities
- Optimization for speed and asynchronous execution

## Citation

```
@article{zhang2025rlm,
  title   = "Recursive Language Models",
  author  = "Zhang, Alex and Khattab, Omar",
  year    = "2025",
  month   = "October",
  url     = "https://alexzhang13.github.io/blog/2025/rlm/"
}
```

---

**Authors:** Alex L. Zhang (MIT CSAIL), Omar Khattab (MIT CSAIL)
**Published:** October 15, 2025
