
# ReBio

**Graph-Centered, Human-in-the-Loop Agentic AI for Protein-Centric Drug Discovery**

---

## Overview

ReBio is an agentic AI framework for protein-centric drug discovery and biomedical reasoning.
It is designed to move beyond prediction-only models by providing explicit, structured, and traceable biological evidence that supports each hypothesis.

Rather than relying on end-to-end deep learning or free-form LLM reasoning, ReBio places a biological knowledge graph at the center of inference, constraining large language models to operate strictly within evidence-supported boundaries.

When automated reasoning is insufficient, the system explicitly defers to human-in-the-loop (HITL) intervention, preventing silent failure and hallucinated conclusions.

ReBio is built on the Helicon multi-agent architecture, which decomposes scientific reasoning into modular, inspectable stages aligned with real-world research workflows.

---

## Key Principles

### Evidence over Prediction

ReBio prioritizes mechanistic explanations and traceable evidence paths over raw predictive accuracy.
Every result is accompanied by graph-derived relationships and scored evidence paths.

### Graph-Centered Reasoning

A biological knowledge graph (Neo4j) serves as the backbone of the system.
LLMs are used as interpreters and synthesizers—not as autonomous decision-makers.

### Hierarchical Evidence Integration

Evidence is explicitly separated into:

* **Primary evidence**: graph relationships and evidence paths
* **Secondary evidence**: external literature and clinical data

This prevents heterogeneous sources from being conflated during reasoning.

### Human-in-the-Loop Safety

When required inputs or sufficient evidence are missing, ReBio halts automatic execution and requests human input.
This design reflects real research practices and ensures accountability.

---

## System Architecture

ReBio follows a multi-agent pipeline, where each node is responsible for a single stage of reasoning:

```
User Query
  ↓
IntentNode
  → classify biomedical intent
  ↓
EntityNode
  → extract and normalize biological entities
  ↓
VisionNode (optional)
  → analyze experimental figures
  ↓
GraphNode
  → graph-based biological inference
  ↓
EvidenceNode
  → multi-hop evidence path discovery & scoring
  ↓
CrawlerNode
  → external knowledge augmentation
  ↓
DesignNode (optional)
  → protein sequence redesign (BioMistral + ESM2)
  ↓
StructureNode (optional)
  → structure prediction (ESMFold)
  ↓
ReasonerNode
  → mechanistic synthesis (LLM-constrained)
  ↓
FinalNode
  → Markdown + JSON report
```

Execution flow is dynamically controlled by a **SupervisorNode**, which handles:

* conditional routing
* loop prevention
* HITL escalation

---

## Core Components

### Graph Reasoning

* Neo4j-based biological knowledge graph
* Typed relationships (TARGETS, BINDS, MODULATES, etc.)
* Multi-hop evidence path discovery
* Path scoring with:

  * hop penalties
  * relationship weights
  * similarity propagation
* Statistical normalization (z-scores)

---

### Protein Design & Evaluation

* Sequence generation using a protein-specialized language model (BioMistral)
* Sequence plausibility scoring with ESM2
* Relative score improvement against wild-type sequences

---

### Structure Prediction

* End-to-end protein structure prediction using ESMFold
* Lazy-loading to minimize computational overhead

---

### Reasoning Engine

Two-stage reasoning:

1. Evidence integration and summarization
2. Mechanistic hypothesis generation

Explicit constraints prevent unsupported claims.

---

## Outputs

ReBio produces dual-format outputs:

### Human-readable Report (Markdown)

* Intent summary
* Extracted entities
* Graph results
* Evidence paths
* Mechanistic reasoning
* Protein design and structure results (if applicable)

### Machine-readable Artifact (JSON)

* Complete intermediate and final results
* Enables reproducibility, evaluation, and downstream analysis

---

## Evaluation Philosophy

ReBio is evaluated not only on retrieval or prediction performance, but also on:

* Evidence strength and path quality
* Mechanistic interpretability
* Failure detection and HITL activation
* Computational efficiency at the node level

This reflects the requirements of real-world biomedical research rather than benchmark-only optimization.

---
