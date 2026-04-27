"""E-07: CPU retopology of Hunyuan3D mesh using trimesh's quadric simplification.

PyMeshLab is GUI-blocked on this container (libharfbuzz). Instant Meshes
binary has no ARM build. We use trimesh's `simplify_quadric_decimation`
which is identical to MeshLab's quadric edge collapse, just CPU-only.

This produces TRIs (not quads). For animation rigging, tris are fine —
the limitation is edge flow (less aesthetic, but functional for skinning).
"""
import time, sys, csv
from pathlib import Path
import trimesh

ROOT = Path("/workspace/character-engine")
IN = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-A-3D/E-05-hunyuan3d/samples/03_alice_textured.glb"
OUT = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/path-A-3D/E-07-retop"
SAMPLES = OUT / "samples"
SAMPLES.mkdir(parents=True, exist_ok=True)

print(f"loading {IN.name}...")
scene = trimesh.load(IN)
mesh = list(scene.geometry.values())[0]
print(f"original: V={len(mesh.vertices):,} F={len(mesh.faces):,}, watertight={mesh.is_watertight}")

# Quadric decimation to multiple target sizes — comparison
TARGETS = [50000, 20000, 8000, 5000]

results = []
for target in TARGETS:
    t0 = time.time()
    simplified = mesh.simplify_quadric_decimation(face_count=target)
    elapsed = time.time() - t0
    nv, nf = len(simplified.vertices), len(simplified.faces)
    out_path = SAMPLES / f"alice_retop_{nf:05d}f.obj"
    simplified.export(out_path)
    print(f"target={target:>6}: actual F={nf:,}, V={nv:,}, time={elapsed:.1f}s")
    results.append({"target": target, "actual_faces": nf, "vertices": nv,
                    "decim_ratio": nf / len(mesh.faces), "time_s": elapsed,
                    "path": str(out_path)})

# Persist metrics
csv_path = ROOT / "pgx_reports/2026-04-27-paradigm-comparison/RAW_NUMBERS.csv"
with open(csv_path, "a") as f:
    w = csv.writer(f)
    for r in results:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        w.writerow(["E-07", "retop_actual_faces", r["actual_faces"], "count", 1,
                   f"target={r['target']} (trimesh quadric)", ts])
        w.writerow(["E-07", "retop_time", r["time_s"], "seconds", 1,
                   f"target={r['target']} faces", ts])

print("\nE-07 done. Retopped meshes saved.")
print(f"Original: 418,300 → smallest target produced {results[-1]['actual_faces']} faces")
print(f"Decimation ratio range: {results[0]['decim_ratio']:.1%} to {results[-1]['decim_ratio']:.2%}")
