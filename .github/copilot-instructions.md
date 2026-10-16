# Repository Instructions: CSAI 380 Exercise Authoring

This repository contains prototype Skill Practice assignments for CSAI 380 (AI Operations on GKE/GCP with Terraform and GitHub Actions). Follow these rules for all work in this repo.

## Core policy: tested or not done

- **We only publish exercises that we have tested and verified actually work.** An exercise is not done until every command, manifest, Terraform configuration, workflow, and DAG in it has been executed successfully against a real GKE/GCP environment.
- Every assignment file (`N.4-*.md`) must carry a status banner immediately below its title:
  - `🚧 DRAFT — not yet tested end-to-end` — instructions written, verification pending.
  - `✅ VERIFIED <YYYY-MM-DD>` — every step executed successfully; include the date and the environment (cluster/GCP project) it was verified against.
- Never flip a banner to VERIFIED without actually running the steps. Never remove a DRAFT banner as part of an unrelated edit.
- When an exercise changes, its status reverts to DRAFT until re-tested.

## Starter files

- Every file an exercise tells students to use, copy, or complete **must exist in this repository** under `starter/`, which mirrors the layout of the student repository:
  - `starter/terraform/` — Terraform for student-scoped resources (namespace, Artifact Registry, GCS bucket)
  - `starter/k8s/` — Kubernetes manifests (`stateful/`, `kafka/` subdirectories per week)
  - `starter/helm/` — Helm values files (Airflow, Kafka)
  - `starter/dags/` — Airflow DAGs
  - `starter/app/` + `starter/Dockerfile` — the sample application students containerize
  - `starter/.github/workflows/` — GitHub Actions workflows (kept under `starter/` so they do not execute in this repo)
- Placeholders students must replace are written as `<angle-brackets>` (e.g., `<your-namespace>`); TODOs students must implement are marked `# TODO(student):`.
- When an exercise references a starter file, link it by repo-relative path so the reference can be verified.

## Security rules for starter content

- **Never touch the `default` namespace.** It contains real (non-exercise) workloads and data. All exercise and verification resources live in dedicated namespaces (e.g., the student's username namespace, `verify-stedi`); never deploy to, scale, or delete anything in `default`.
- Never commit credentials, service-account keys, tokens, or `.tfstate` files — the starter `.gitignore` must cover these.
- Secrets in manifests must use `secretKeyRef` / GitHub Actions secrets; never inline passwords, even as examples.
- Anything insecure-by-design for teaching (single-node MySQL, public load balancer) must say so explicitly in the exercise text.

## Teacher notes and solutions

- When an exercise is finished (tested and verified), write teacher notes in a separate README under a `solutions/` directory, one subdirectory per exercise: `solutions/N.4/README.md`.
- Each solutions README must include:
  - **Solutions** — the completed commands, manifests, code, or configuration for every student-facing step, including completed versions of any `# TODO(student)` stubs.
  - **Gotchas** — pitfalls students may encounter, discovered during verification testing (e.g., Apple Silicon images crashing on amd64 nodes, GCE quota scale-up failures, chart key renames), each with its symptom and fix.
- Keep solutions out of `starter/` — students receive starter files, not solutions.

## The STEDI application

- The application referenced throughout these exercises is the **stedi-private** project located adjacent to this repository (`../stedi-private`). It is the source of truth for environment variable names (`REDIS_HOST`, `REDIS_PASSWORD`, `KAFKA_BROKER`, `KAFKA_RISK_TOPIC`), the `/simulation` toggle endpoints, the listening port (4567), and deployment patterns (`app.yaml`).
- When authoring or changing exercises that involve the STEDI codebase — which image students deploy, what parts of stedi-private get copied into `starter/`, how it participates in a given week's project stage — **prompt the user for a decision** rather than assuming. Its code and configuration may change independently of this repo.

## AI Ops dual thread

Every assignment must reinforce **AI Ops in both senses**, each week:

- **(a) Use an agent to do the ops** — how students can use an AI agent (and agent loops: prompt → inspect → verify against the real system → re-prompt) to help with that week's steps, with the standing rule that students verify agent output before acting on it and are accountable for everything they apply.
- **(b) Build infrastructure that AI operations run on** — why that week's skill matters for infrastructure that supports AI operations (model serving, feature stores, training/data pipelines, real-time scoring, feature staleness, etc.).

Mechanically, each assignment carries:

- An `## AI Ops in This Assignment:` section between `## Purpose:` and `## Instructions:` covering both senses with week-specific content.
- A required **AI Ops reflection** in the week's evidence file: one verified agent-assisted step (prompt, output, verification) plus a week-specific AI-relevance question.
- Rubric coverage: the AI Ops reflection is graded inside the third criterion.

New or revised assignments must keep all three elements.

## Conventions

- Assignments follow the W26 Canvas template: `# N.4 Title`, `## Purpose:`, `## AI Ops in This Assignment:`, `## Instructions:`, `## Grading` with a 15-point rubric (three criteria at 5/3/1/0).
- All student work is submitted as a GitHub repository link; exercises must keep the IaC + GitHub Actions thread consistent week to week.
- Flat file naming in repo root: `N.4-<slug>.md`.
