#!/usr/bin/env python3
"""Structural analysis script for architecture-analyzer agent.

Usage: python3 ua-arch-analyze.py <input_json> <output_json>
"""
import json
import sys
from pathlib import Path

PATTERN_MAP = {
    "routes": "api", "api": "api", "controllers": "api", "endpoints": "api",
    "handlers": "api", "serializers": "api", "blueprints": "api", "routers": "api",
    "services": "service", "core": "service", "lib": "service", "domain": "service",
    "logic": "service", "signals": "service", "internal": "service", "composables": "service",
    "models": "data", "db": "data", "data": "data", "persistence": "data",
    "repository": "data", "entities": "data", "migrations": "data", "sql": "data",
    "schema": "data", "entity": "data", "database": "data",
    "utils": "utility", "helpers": "utility", "common": "utility", "shared": "utility",
    "tools": "utility", "pkg": "utility", "templatetags": "utility",
    "config": "config", "constants": "config", "env": "config", "settings": "config",
    "management": "config", "commands": "config",
    "tests": "test", "test": "test", "spec": "test", "specs": "test",
    "types": "types", "interfaces": "types", "contracts": "types", "dtos": "types",
    "dto": "types", "request": "types", "response": "types",
    "components": "ui", "views": "ui", "pages": "ui", "ui": "ui",
    "layouts": "ui", "screens": "ui",
    "middleware": "middleware", "plugins": "middleware", "interceptors": "middleware",
    "guards": "middleware",
    "hooks": "hooks",
    "store": "state", "state": "state", "reducers": "state", "actions": "state",
    "slices": "state",
    "assets": "assets", "static": "assets", "public": "assets",
    "cmd": "entry", "bin": "entry",
    "docs": "documentation", "documentation": "documentation", "wiki": "documentation",
    "deploy": "infrastructure", "deployment": "infrastructure", "infra": "infrastructure",
    "infrastructure": "infrastructure", "docker": "infrastructure",
    "k8s": "infrastructure", "kubernetes": "infrastructure", "helm": "infrastructure",
    "charts": "infrastructure", "terraform": "infrastructure", "tf": "infrastructure",
    "ai": "service",
    "memory": "data",
    "prompts": "config",
}

def get_first_dir(path, common_prefix_parts):
    """Get first directory segment after the common prefix."""
    parts = path.split("/")
    # If common prefix has parts, skip them
    skip = len(common_prefix_parts)
    if skip > 0 and parts[:skip] == common_prefix_parts:
        parts = parts[skip:]
    # Return first segment (could be a filename if at root)
    if len(parts) >= 2:
        return parts[0]
    return "root"


def classify_file_pattern(file_path):
    """Classify file-level patterns for test files, entry points, etc."""
    name = Path(file_path).name
    if name.startswith("test_") or name.endswith("_test.py") or ".test." in name or ".spec." in name:
        return "test"
    if name == "__init__.py":
        return "entry"
    if name == "config.py" or name == "constants.py":
        return "config"
    return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 ua-arch-analyze.py <input_json> <output_json>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "r") as f:
        data = json.load(f)

    file_nodes = data["fileNodes"]
    import_edges = data.get("importEdges", [])
    all_edges = data.get("allEdges", [])

    # Build file ID lookup
    file_by_id = {n["id"]: n for n in file_nodes}

    # A. Directory Grouping
    # Find common path prefix
    paths = [n["filePath"] for n in file_nodes]
    min_parts = min(len(p.split("/")) for p in paths)
    common_prefix = ""
    common_parts = []
    if min_parts > 1:
        first_parts = paths[0].split("/")
        for i in range(min_parts - 1):
            segment = first_parts[i]
            if all(p.split("/")[i] == segment for p in paths):
                common_parts.append(segment)
            else:
                break
        common_prefix = "/".join(common_parts) + "/" if common_parts else ""

    directory_groups = {}
    for n in file_nodes:
        group = get_first_dir(n["filePath"], common_parts)
        directory_groups.setdefault(group, []).append(n["id"])

    # B. Node Type Grouping
    node_type_groups = {}
    for n in file_nodes:
        t = n["type"]
        node_type_groups.setdefault(t, []).append(n["id"])

    # C. Import Adjacency Matrix
    import_map = {}
    fan_in = {}
    fan_out = {}
    for n in file_nodes:
        nid = n["id"]
        import_map.setdefault(nid, {"imports": [], "imported_by": []})
        fan_in.setdefault(nid, 0)
        fan_out.setdefault(nid, 0)

    for edge in import_edges:
        src = edge["source"]
        tgt = edge["target"]
        # Only count file->file imports
        if src.startswith("file:") and tgt.startswith("file:"):
            if src not in import_map:
                import_map[src] = {"imports": [], "imported_by": []}
            if tgt not in import_map:
                import_map[tgt] = {"imports": [], "imported_by": []}
            import_map[src]["imports"].append(tgt)
            import_map[tgt]["imported_by"].append(src)
            fan_out[src] = fan_out.get(src, 0) + 1
            fan_in[tgt] = fan_in.get(tgt, 0) + 1

    # D. Cross-Category Dependency Analysis
    cross_category = {}
    for edge in all_edges:
        src = edge["source"]
        tgt = edge["target"]
        src_type = src.split(":")[0]
        tgt_type = tgt.split(":")[0]
        if src_type != tgt_type:
            key = f"{src_type} -> {tgt_type}"
            edge_type = edge["type"]
            if key not in cross_category:
                cross_category[key] = {"fromType": src_type, "toType": tgt_type, "edgeType": edge_type, "count": 0}
            cross_category[key]["count"] += 1

    cross_category_edges = sorted(cross_category.values(), key=lambda x: -x["count"])

    # E. Inter-Group Import Frequency
    group_of = {}
    for group, ids in directory_groups.items():
        for nid in ids:
            group_of[nid] = group

    inter_group = {}
    for edge in import_edges:
        src = edge["source"]
        tgt = edge["target"]
        if src.startswith("file:") and tgt.startswith("file:"):
            src_g = group_of.get(src, "root")
            tgt_g = group_of.get(tgt, "root")
            if src_g != tgt_g:
                key = f"{src_g} -> {tgt_g}"
                if key not in inter_group:
                    inter_group[key] = {"from": src_g, "to": tgt_g, "count": 0}
                inter_group[key]["count"] += 1

    inter_group_list = sorted(inter_group.values(), key=lambda x: -x["count"])

    # F. Intra-Group Import Density
    intra_group = {}
    for group, ids in directory_groups.items():
        internal = 0
        total = 0
        for edge in import_edges:
            src = edge["source"]
            tgt = edge["target"]
            if src.startswith("file:") and tgt.startswith("file:"):
                src_g = group_of.get(src, "root")
                tgt_g = group_of.get(tgt, "root")
                if src_g == group or tgt_g == group:
                    total += 1
                    if src_g == group and tgt_g == group:
                        internal += 1
        density = internal / total if total > 0 else 0
        intra_group[group] = {"internalEdges": internal, "totalEdges": total, "density": round(density, 2)}

    # G. Directory Pattern Matching
    pattern_matches = {}
    for group in directory_groups:
        pattern_matches[group] = PATTERN_MAP.get(group, classify_file_pattern(group) or "other")

    # H. Deployment Topology
    deployment_topology = {
        "hasDockerfile": False,
        "hasCompose": False,
        "hasK8s": False,
        "hasTerraform": False,
        "hasCI": False,
        "infraFiles": []
    }

    # I. Data Pipeline Detection
    data_pipeline = {
        "schemaFiles": [],
        "migrationFiles": [],
        "dataModelFiles": [],
        "apiHandlerFiles": []
    }
    for n in file_nodes:
        p = n["filePath"]
        if "schema" in p.lower() or "migration" in p.lower():
            if "migration" in p.lower():
                data_pipeline["migrationFiles"].append(p)
            else:
                data_pipeline["schemaFiles"].append(p)
        if "model" in n["id"] or "models" in n["id"]:
            data_pipeline["dataModelFiles"].append(n["id"])
        if n["id"].startswith("file:handlers/") and n["id"] != "file:handlers/__init__.py":
            data_pipeline["apiHandlerFiles"].append(n["id"])

    # J. Documentation Coverage
    groups_with_docs = set()
    undocumented = []
    for group, ids in directory_groups.items():
        has_readme = False
        for nid in ids:
            if nid.startswith("document:"):
                groups_with_docs.add(group)
                has_readme = True
        if not has_readme:
            undocumented.append(group)
    total_groups = len(directory_groups)
    doc_coverage = {
        "groupsWithDocs": len(groups_with_docs),
        "totalGroups": total_groups,
        "coverageRatio": round(len(groups_with_docs) / total_groups, 2) if total_groups > 0 else 0,
        "undocumentedGroups": undocumented
    }

    # K. Dependency Direction
    dep_direction = []
    dep_count = {}
    for item in inter_group_list:
        f = item["from"]
        t = item["to"]
        count = item["count"]
        rev_key = f"{t} -> {f}"
        rev_count = inter_group.get(rev_key, {}).get("count", 0)
        if count > rev_count:
            dep_direction.append({"dependent": f, "dependsOn": t})
        elif rev_count > count:
            dep_direction.append({"dependent": t, "dependsOn": f})

    # Stats
    file_stats = {
        "totalFileNodes": len(file_nodes),
        "filesPerGroup": {g: len(ids) for g, ids in directory_groups.items()},
        "nodeTypeCounts": {t: len(ids) for t, ids in node_type_groups.items()}
    }

    result = {
        "scriptCompleted": True,
        "directoryGroups": directory_groups,
        "nodeTypeGroups": node_type_groups,
        "crossCategoryEdges": cross_category_edges,
        "interGroupImports": inter_group_list,
        "intraGroupDensity": intra_group,
        "patternMatches": pattern_matches,
        "deploymentTopology": deployment_topology,
        "dataPipeline": data_pipeline,
        "docCoverage": doc_coverage,
        "dependencyDirection": dep_direction,
        "fileStats": file_stats,
        "fileFanIn": dict(sorted(fan_in.items(), key=lambda x: -x[1])),
        "fileFanOut": dict(sorted(fan_out.items(), key=lambda x: -x[1]))
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Analysis complete. Results written to {output_path}")

if __name__ == "__main__":
    main()
