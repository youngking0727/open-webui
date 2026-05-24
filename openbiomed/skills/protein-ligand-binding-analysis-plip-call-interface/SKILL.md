---
name: protein-ligand-binding-analysis-plip-call-interface
description: >
  Call interface for OpenBioMed protein-ligand binding analysis (PLIP via protein_ligand_analysis task).
  Calls the /run_pipeline/ endpoint of any OpenBioMed-compatible HTTP service.
  Endpoint is configurable for cloud, self-hosted, or local deployment, independent of server implementation.
  Use this skill when:
  (1) Analyzing binding interactions from a PDB structure file,
  (2) Identifying hydrogen bonds, hydrophobic contacts, π-stacking, salt bridges, and water bridges,
  (3) Generating interaction summary reports for drug discovery.
license: MIT
category: binding-affinity
tags: [protein-ligand, interaction-analysis, plip, binding, drug-discovery]
---

# Protein-Ligand Binding Analysis - PLIP Call Interface

Analyze protein-ligand interactions in PDB structures via the `/run_pipeline/` endpoint of an OpenBioMed service with `task="protein_ligand_analysis"`.

## Endpoint Configuration (read this first)

Defaults declared in this skill (edit these inline when the real values are known):

- `OPENBIOMED_CLOUD_URL = http://127.0.0.1:8092`
  Placeholder for the OpenBioMed cloud service base URL. Replace with the real published URL when available.

This skill does NOT hardcode the endpoint at the call sites. Before calling the API, resolve the base URL in this order:

1. If the user explicitly provides an endpoint in the current conversation, use it.
2. Otherwise, use the environment variable `OPENBIOMED_API_BASE_URL` if it is set in the runtime environment.
3. Otherwise, ask the user once which endpoint to use, and offer these options:
   - **OpenBioMed cloud service** (default, hosted): the `OPENBIOMED_CLOUD_URL` value declared above.
   - **Self-hosted OpenBioMed server**: the user provides their own base URL, e.g. `http://localhost:9000` or `https://openbiomed.internal.example.com`.
4. Remember the chosen base URL for the rest of the session and reuse it for subsequent calls without re-asking.

Privacy note: if the PDB structure or compound data is proprietary or unpublished, recommend a self-hosted endpoint rather than the public cloud service, and let the user confirm before sending.

In the rest of this document, `${OPENBIOMED_API_BASE_URL}` is a placeholder for the resolved base URL (no trailing slash). The full endpoint is therefore `${OPENBIOMED_API_BASE_URL}/run_pipeline/`.

## When to Use

- Analyzing binding modes from crystal structures or docking results
- Identifying key interactions driving binding affinity
- Comparing ligand binding patterns across multiple structures
- Generating interaction reports for drug discovery

## API Parameters

**Required parameters:**
- `task`: "protein_ligand_analysis"
- `protein`: PDB file path (local file path to .pdb file)

**Optional parameters:**
- `model`: Model name (optional, for future use)

```json
{
  "task": "protein_ligand_analysis",
  "model": "plip",
  "protein": "/path/to/your/protein.pdb"
}
```

## API Call Examples

### 1. Basic Binding Analysis

```bash
curl -X 'POST' \
  '${OPENBIOMED_API_BASE_URL}/run_pipeline/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "task": "protein_ligand_analysis",
  "model": "plip",
  "protein": "/path/to/your/complex.pdb"
}'
```

### 2. Analyze EGFR-Ligand Complex (1M17)

```bash
curl -X 'POST' \
  '${OPENBIOMED_API_BASE_URL}/run_pipeline/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "task": "protein_ligand_analysis",
  "model": "plip",
  "protein": "./pdb/1m17.pdb"
}'
```

### 3. Analyze Kinase-Inhibitor Binding

```bash
curl -X 'POST' \
  '${OPENBIOMED_API_BASE_URL}/run_pipeline/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "task": "protein_ligand_analysis",
  "model": "plip",
  "protein": "./pdb/kinase_inhibitor.pdb"
}'
```

## Response Format

The API returns a JSON object containing:

```json
{
  "task": "protein_ligand_analysis",
  "num_binding_sites": 2,
  "interactions": [
    {
      "ligand_id": "ERL",
      "h_bonds": 5,
      "hydrophobic": 8,
      "pi_stacking": 2,
      "salt_bridges": 1,
      "water_bridges": 3,
      "details": "Detailed interaction report..."
    }
  ]
}
```

## Interaction Types Reported

| Type | Description |
|------|-------------|
| Hydrogen bonds | H-bonds with ligand/protein as donor |
| Hydrophobic contacts | Non-polar interactions |
| Water bridges | Water-mediated interactions |
| π-stacking | Aromatic ring interactions |
| Salt bridges | Ionic interactions |

## Common Use Cases

### 1. Drug-Target Binding Analysis

Analyze how a drug molecule binds to its protein target.

```bash
curl -X 'POST' \
  '${OPENBIOMED_API_BASE_URL}/run_pipeline/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "task": "protein_ligand_analysis",
  "model": "plip",
  "protein": "./docking_results/complex_docked.pdb"
}'
```

### 2. Fragment-Based Drug Design

Analyze fragment binding interactions.

```bash
curl -X 'POST' \
  '${OPENBIOMED_API_BASE_URL}/run_pipeline/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "task": "protein_ligand_analysis",
  "model": "plip",
  "protein": "./fragments/fragment_screening.pdb"
}'
```

### 3. Mutagenesis Impact Analysis

Compare wild-type and mutant binding.

```bash
curl -X 'POST' \
  '${OPENBIOMED_API_BASE_URL}/run_pipeline/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "task": "protein_ligand_analysis",
  "model": "plip",
  "protein": "./mutants/mutant_complex.pdb"
}'
```

## Limitations

- Requires a valid PDB file with protein-ligand complex
- Ligands must be present as HETATM records in the PDB file
- Very large complexes may take longer to process
- Some malformed PDB files may fail to parse

## Related Skills

- `protein-molecule-docking-score`: For binding affinity scoring
- `protein-binding-site-prediction`: For identifying binding sites
- `structure-prediction-boltz-2`: For protein structure prediction
- `target-based-lead-design`: For structure-based drug design
