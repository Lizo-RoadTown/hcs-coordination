# Decompose and reconstruct a prototype

Status: Working procedure, version 0.1. Owner: lead repository for the reconstruction.

Use this procedure to recover capabilities from existing projects, establish their responsibilities, and assemble them into a maintained rapid prototyping toolkit. Components may begin in separate repositories and later consolidate into one repository and library. Extract and integrate useful components while decomposition continues; finalize responsibility-based names after the full agreed decomposition scope is accounted for.

This procedure is intended for the decomposition module to distribute by reference. Its current location is a staging home in Tapestry; relocation to that module is pending identification of its canonical repository and path. No script implements this procedure yet.

## 1. Establish the reconstruction scope

Record the source repositories and revisions, the lead repository, destination system, intended users, and capabilities to preserve. Define concrete workflows that must work after reconstruction, with observable outcomes. Identify live deployments and data that must remain available during the work.

Separate the toolkit from its applications: reusable components provide capabilities; an assembled application configures and connects selected capabilities for a purpose. Record whether each application supports one person across projects, one shared project across contributors, or another explicitly defined scope. Preserve those scopes when components are shared.

Record existing authorization for extraction, changes, releases, and retirement. Work within that scope without repeatedly asking for permission. Escalate genuinely new scope or actions outside the authorization. Writing this procedure does not itself authorize migrating or retiring a particular service.

**Exit check:** the lead repository has a versioned scope record and at least one executable acceptance scenario. Define the actual operational requirements associated with “enterprise-ready,” such as access isolation, recovery, expected load, support ownership, or availability; evaluate each against evidence later.

## 2. Inventory what actually exists

For every source, examine code, configuration, migrations, tests, deployment definitions, and available runtime evidence. Record an evidence location and revision for each assertion. Distinguish code existing from code running successfully.

Inventory:

- Entry points, services, packages, scripts, plugins, skills, hooks, and scheduled jobs.
- Data stores, schemas, migrations, identities, and retention rules.
- Inputs, outputs, actual consumers, and dependencies.
- Automatic triggers, manual invocations, and work requiring an agent session.
- Credentials by reference and required permissions; never include secret values.
- Deployment owners, source revisions, endpoint names, and release mechanisms.
- Duplicate implementations, dead ends, placeholders, and unresolved behavior.

Use separate fields for implementation state, deployment state, and trigger type. A tested classifier can be implemented but undeployed; a deployed script can still be manual. Unknown is a valid state and must not be silently converted into working or absent.

Trace every important output to a reader. Mark discarded outputs, unread files, and missing transitions explicitly.

**Exit check:** every in-scope entry point and store is accounted for, with unknowns listed. Important workflow transitions have evidence of their actual behavior or an explicit gap.

## 3. Decompose by responsibility

Identify what each component does, what state it owns, and the interfaces through which it interacts. Do not assume directories, repository names, or deployment names define the right component boundaries.

Separate reusable mechanics from domain content and deployment configuration. For example, a correction-processing mechanism can be reusable while tutoring preferences remain personal content. Keep tightly coupled implementation details together when separating them would add coordination without useful independence.

Assign stable component IDs before changing names. IDs remain stable through renames, moves, and consolidation. Record source locations and revision history so extraction retains provenance.

For each connection, record producer, consumer, contract, identity fields, trigger, transport, access scope, delivery behavior, failure handling, and evidence. Check that the consumer can interpret what the producer actually emits. A delivered event with no usable artifact identity is not a working analysis input.

**Exit check:** components have bounded responsibilities; state ownership and connections are explicit; all source inventory items map to a component or an explained disposition.

## 4. Decide what happens to each component

Record two decisions separately:

| Decision | Allowed values |
|---|---|
| Destination | Retain in current home, extract into toolkit, consolidate with an existing component, retire, or defer with a reason |
| Implementation treatment | Lift, refactor, rewrite, or not applicable |

Before creating a reusable component, search the toolkit inventory for an existing capability with the same responsibility. Select one canonical implementation. A temporary extraction copy must have a named authority, a transition plan, and a removal condition.

Prioritize components needed for the first complete acceptance workflow. Record dependent work and migration order. Keep unrelated improvements out of the extraction change.

**Exit check:** every component has a disposition, destination or deferral reason, responsible owner, and scoped implementation treatment.

## 5. Define contracts and extract incrementally

Define inputs, outputs, errors, version compatibility, identity, configuration, and state ownership before connecting components. Specify whether each component is a library module, executable, service, plugin, or domain payload. One toolkit repository can contain several of these forms.

Extract one bounded capability at a time. Preserve license and provenance requirements. Remove source-project assumptions from reusable mechanics and expose the necessary configuration. Add meaningful checks for preserved behavior and changed interfaces.

For persistent state, define migration ownership, migration ordering, schema compatibility, backup, and rollback behavior. Check destination service names and endpoints for collisions before deployment.

**Exit check:** the component can be built or installed from its declared source with documented dependencies. Its interface checks pass and its original behavior is preserved or explicitly superseded.

## 6. Assemble and prove a working workflow

Connect the selected components into the target application. For each transition identify what starts it and what constitutes completion. An instruction to an agent is not an automatic trigger unless a running mechanism invokes that agent with the needed context, tools, and execution permissions.

For unattended workflows, define delivery acknowledgement, retries, deduplication, timeouts, recovery after interruption, and visible terminal failures. Record which process owns completing the workflow. Avoid duplicate actors applying the same change concurrently.

For the personal self-improvement application, the required path is:

1. A hook or scheduled job captures activity or a correction with its context.
2. The observation is stored with stable identity and evidence.
3. Analysis identifies the support or structural change needed.
4. The creation mechanism builds or updates the appropriate skill, hook, tool, or workflow.
5. Validation checks the change and its effect on existing behavior.
6. The delivery mechanism installs or activates the version within established permissions.
7. Later observations evaluate its use and effect; unsuccessful changes trigger revision or rollback.

Producing a finding or candidate is an intermediate state. No extra user prompt should be required to advance routine authorized work. Decisions outside established authority become explicit exceptions; unrelated work continues.

For a shared project application, observation concerns knowledge exchanges at project interfaces. Reuse mechanics without granting access to contributors' private context or unrelated projects.

**Exit check:** a real initiating event reaches the intended outcome. Evidence links the initiating event, intermediate records, installed version, and subsequent evaluation. Missing identity, missing instrumentation, observed zero activity, and processing failure remain distinguishable.

## 7. Verify operational readiness

Exercise the declared requirements from step 1. Include the successful path and material failure cases: unavailable dependencies, duplicate delivery, restart during processing, invalid or incompatible input, denied access, failed installation, and rollback.

Verify authentication and access isolation at actual read and write surfaces. Keep secrets in the designated credential mechanism. Demonstrate recovery of persistent state where required. Establish support ownership, release procedures, dependency/version management, and useful operational visibility.

For generated changes, verify behavior rather than merely the existence of a new file. In the tutoring example, confirm that the relevant guidance loads in a later session and assess whether the response follows it. Skill creation alone does not establish behavioral success.

**Exit check:** each readiness requirement has passing evidence or an explicit limitation and responsible owner. “Enterprise-ready” applies only to the requirements actually demonstrated.

## 8. Finalize names and consolidate

After the full agreed decomposition inventory is reconciled, choose names describing the responsibilities established through extraction and use. Preserve stable IDs and maintain old-name aliases where compatibility requires them.

Before renaming, enumerate imports, package names, filesystem paths, API routes, service names, deployment settings, persisted namespaces, telemetry labels, automation, documentation, and downstream consumers. Migrate references deliberately; changing a display name must not silently change data identity.

Consolidate components into the toolkit's canonical repository and library structure as appropriate. Keep deployable applications and domain payloads identifiable within that home. Confirm a clean checkout can build the intended distribution and assemble a representative application without source-repository dependencies.

**Exit check:** final names, canonical homes, versions, compatibility mappings, and consumers agree. Consolidation does not leave multiple authoritative implementations.

## 9. Cut over and retire

Switch consumers in bounded increments. Record the active source revision, destination version, migration outcome, and rollback target. Verify behavior in the target environment before declaring cutover complete.

Retire duplicate processes, old dispatch targets, callbacks, and dependencies only under the applicable authorization. Keep historical sources as references when needed; mark their runtime status clearly. Archiving a repository is a separate action from moving one component.

**Exit check:** consumers use the canonical implementation, obsolete automatic jobs are accounted for, and rollback remains possible for the agreed period. No undeclared runtime dependency on a retired source remains.

## 10. Keep the procedure runnable and resumable

Maintain a reconstruction manifest beside each project's decomposition record. The lead repository tracks cross-repository dependencies and completion; source repositories retain links to their component records. Share this procedure by versioned reference rather than maintaining divergent copies.

The following is a proposed record shape for a future runner, not an existing CLI or schema:

```yaml
procedure_version: "0.1"
reconstruction_id: example-reconstruction
lead_repository: example-lead
scope_revision: example-scope-revision
sources:
  - repository: example-source
    revision: example-commit
acceptance_scenarios:
  - id: correction-to-installed-support
    trigger: correction_event
    expected_outcome: support_installed_and_evaluated
components:
  - id: component-001
    provisional_name: correction-processor
    final_name: null
    responsibility: Turn contextual corrections into support changes
    source_locations: []
    canonical_home: null
    implementation_state: unknown
    deployment_state: unknown
    trigger_type: unknown
    disposition: extract
    treatment: refactor
    state_owner: null
    consumers: []
    contracts: []
    evidence: []
    stage: inventoried
    blockers: []
connections: []
decisions: []
authorization_reference: null
```

Each connection record must carry the contract and execution fields defined in step 3. Each stage result must include its input revisions, check results, evidence locations, timestamp, and unresolved blockers.

A future runner should validate records, compute dependency order, run configured checks, persist checkpoints, and resume interrupted work without repeating completed mutations. Changed source revisions invalidate affected evidence and dependent checks. Never mark an unexecuted check as passed. Preserve errors and reasons when a stage is blocked.

Use stage states such as `pending`, `running`, `passed`, `failed`, `blocked`, and `not_applicable`; require a reason for `not_applicable`. Keep the workflow resumable across sessions and repositories. Architectural judgments can be agent-assisted, while deterministic checks verify recorded contracts and actual execution.

## Completion checklist

- [ ] Every source item is mapped, retained, retired, or explicitly deferred.
- [ ] Every retained capability has one canonical owner and implementation.
- [ ] Domain content and private scope remain separate from reusable mechanics.
- [ ] Important connections have compatible contracts and stable identities.
- [ ] Automatic workflows have executable triggers through to their outcomes.
- [ ] Installation and subsequent effect are demonstrated for self-improvement paths.
- [ ] Operational requirements have evidence and limitations are recorded.
- [ ] Final naming and consumer migrations are reconciled.
- [ ] Cutover and rollback are documented; obsolete runtime paths are accounted for.
- [ ] Another project can follow the versioned procedure and resume from its records.

## Tapestry application notes

Apply the current [core directives](CORE_DIRECTIVES.md) and [migration guidance](migration/README.md) when using this procedure in Tapestry. Explicit current operator instructions take precedence over older descriptions. This document establishes a routine; it does not change accepted ADRs or perform a code migration. The operator explicitly authorized drafting this document without Loom Memory access on 2026-10-21.
