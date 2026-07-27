const fs = require('fs');

const inputPath = process.argv[2];
const outputPath = process.argv[3];

if (!inputPath || !outputPath) {
  console.error('Usage: node ua-tour-analyze.js <input.json> <output.json>');
  process.exit(1);
}

let data;
try {
  data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
} catch (e) {
  console.error('Failed to read input:', e.message);
  process.exit(1);
}

const { nodes, edges, layers } = data;

// Build lookup
const nodeMap = {};
for (const n of nodes) {
  nodeMap[n.id] = n;
}

// A. Fan-In: count edges TO each node (only imports/calls types for code relevance)
const fanIn = {};
for (const n of nodes) fanIn[n.id] = 0;
for (const e of edges) {
  if (fanIn[e.target] !== undefined) fanIn[e.target]++;
}
const fanInRanking = Object.entries(fanIn)
  .filter(([id]) => nodeMap[id])
  .sort((a, b) => b[1] - a[1])
  .slice(0, 20)
  .map(([id, count]) => ({ id, fanIn: count, name: nodeMap[id].name }));

// B. Fan-Out: count edges FROM each node
const fanOut = {};
for (const n of nodes) fanOut[n.id] = 0;
for (const e of edges) {
  if (fanOut[e.source] !== undefined) fanOut[e.source]++;
}
const fanOutRanking = Object.entries(fanOut)
  .filter(([id]) => nodeMap[id])
  .sort((a, b) => b[1] - a[1])
  .slice(0, 20)
  .map(([id, count]) => ({ id, fanOut: count, name: nodeMap[id].name }));

// C. Entry Point Candidates
const entryPointScores = {};
for (const n of nodes) entryPointScores[n.id] = 0;

const entryFilePatterns = /^(index|main|app|server|bot)\.(ts|js|py)$/;
const rootEntryPatterns = /^(app\.py|bot\.py|main\.py|run\.py)$/;

for (const n of nodes) {
  let score = 0;
  const name = n.name;
  const fp = n.filePath || '';

  if (n.type === 'file') {
    // Filename match
    if (rootEntryPatterns.test(name)) score += 3;
    else if (entryFilePatterns.test(name)) score += 3;

    // Root or one-level deep
    if (!fp.includes('/')) score += 1;
    else if (fp.split('/').length === 2) score += 1;

    // High fan-out (top 10%)
    const foRank = Object.entries(fanOut).sort((a, b) => b[1] - a[1]);
    const top10 = Math.max(1, Math.ceil(foRank.length * 0.1));
    const isTop10 = foRank.slice(0, top10).some(([id]) => id === n.id);
    if (isTop10) score += 1;

    // Low fan-in (bottom 25%)
    const fiRank = Object.entries(fanIn).sort((a, b) => a[1] - b[1]);
    const bottom25 = Math.max(1, Math.ceil(fiRank.length * 0.25));
    const isBottom25 = fiRank.slice(0, bottom25).some(([id]) => id === n.id);
    if (isBottom25) score += 1;
  }

  if (n.type === 'document') {
    if (n.id === 'document:README.md') score += 5;
    else if (name.endsWith('.md')) score += 2;
  }

  entryPointScores[n.id] = score;
}

const entryPointCandidates = Object.entries(entryPointScores)
  .filter(([id]) => nodeMap[id])
  .sort((a, b) => b[1] - a[1])
  .slice(0, 5)
  .map(([id, score]) => ({ id, score, name: nodeMap[id].name, summary: nodeMap[id].summary }));

// D. BFS Traversal from top CODE entry point
const codeEntries = entryPointCandidates.filter(e => nodeMap[e.id] && nodeMap[e.id].type === 'file');
const bfsStart = codeEntries.length > 0 ? codeEntries[0].id : null;

const bfsResult = { startNode: bfsStart, order: [], depthMap: {}, byDepth: {} };
if (bfsStart) {
  const visited = new Set();
  const queue = [{ id: bfsStart, depth: 0 }];
  visited.add(bfsStart);

  while (queue.length > 0) {
    const { id, depth } = queue.shift();
    bfsResult.order.push(id);
    bfsResult.depthMap[id] = depth;
    if (!bfsResult.byDepth[depth]) bfsResult.byDepth[depth] = [];
    bfsResult.byDepth[depth].push(id);

    // Find all imports/calls edges FROM this node
    const targets = edges
      .filter(e => e.source === id && (e.type === 'imports' || e.type === 'calls') && !visited.has(e.target) && nodeMap[e.target] && nodeMap[e.target].type === 'file')
      .map(e => e.target);

    for (const t of targets) {
      visited.add(t);
      queue.push({ id: t, depth: depth + 1 });
    }
  }
}

// E. Non-Code File Inventory
const nonCodeFiles = { documentation: [], infrastructure: [], data: [], config: [] };
for (const n of nodes) {
  if (n.type === 'document') {
    nonCodeFiles.documentation.push({ id: n.id, name: n.name, type: n.type, summary: n.summary });
  } else if (n.type === 'config') {
    nonCodeFiles.config.push({ id: n.id, name: n.name, type: n.type, summary: n.summary });
  } else if (['service', 'pipeline', 'resource'].includes(n.type)) {
    nonCodeFiles.infrastructure.push({ id: n.id, name: n.name, type: n.type, summary: n.summary });
  } else if (['table', 'schema', 'endpoint'].includes(n.type)) {
    nonCodeFiles.data.push({ id: n.id, name: n.name, type: n.type, summary: n.summary });
  }
}

// F. Clusters: find groups of nodes with many edges between them
// Look for node pairs that have bidirectional relationships (A imports B AND B imports A or A calls B)
// Then expand by adding nodes connected to 2+ cluster members
const fileNodeIds = new Set(nodes.filter(n => n.type === 'file').map(n => n.id));

// Build adjacency map for import/calls edges among file nodes
const adj = {};
for (const n of nodes) {
  if (n.type === 'file') adj[n.id] = new Set();
}
for (const e of edges) {
  if (adj[e.source] && adj[e.target] && (e.type === 'imports' || e.type === 'calls')) {
    adj[e.source].add(e.target);
  }
}

// Find bidirectional pairs
const pairs = [];
const fileIds = Array.from(fileNodeIds);
for (let i = 0; i < fileIds.length; i++) {
  for (let j = i + 1; j < fileIds.length; j++) {
    const a = fileIds[i], b = fileIds[j];
    if (adj[a].has(b) && adj[b].has(a)) {
      pairs.push([a, b]);
    }
  }
}

// Expand clusters
const clusters = [];
const usedInCluster = new Set();
for (const [a, b] of pairs) {
  if (usedInCluster.has(a) || usedInCluster.has(b)) continue;
  const cluster = new Set([a, b]);
  // Expand: add nodes connected to 2+ cluster members
  let changed = true;
  while (changed) {
    changed = false;
    for (const nid of fileIds) {
      if (cluster.has(nid)) continue;
      let connections = 0;
      for (const member of cluster) {
        if (adj[nid].has(member) || adj[member].has(nid)) connections++;
      }
      if (connections >= 2) {
        cluster.add(nid);
        changed = true;
      }
    }
  }
  const nodeList = Array.from(cluster);
  for (const nid of nodeList) usedInCluster.add(nid);
  clusters.push({ nodes: nodeList, edgeCount: edges.filter(e => (e.type === 'imports' || e.type === 'calls') && nodeList.includes(e.source) && nodeList.includes(e.target)).length });
}

clusters.sort((a, b) => b.edgeCount - a.edgeCount);
const topClusters = clusters.slice(0, 10);

// G. Layers
const layerData = {
  count: layers.length,
  list: layers.map(l => ({ id: l.id, name: l.name, description: l.description }))
};

// H. Node Summary Index
const nodeSummaryIndex = {};
for (const n of nodes) {
  nodeSummaryIndex[n.id] = { name: n.name, type: n.type, summary: n.summary };
}

const result = {
  scriptCompleted: true,
  entryPointCandidates,
  fanInRanking,
  fanOutRanking,
  bfsTraversal: bfsResult,
  nonCodeFiles,
  clusters: topClusters,
  layers: layerData,
  nodeSummaryIndex,
  totalNodes: nodes.length,
  totalEdges: edges.length
};

fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
console.log('Analysis complete.');
process.exit(0);
