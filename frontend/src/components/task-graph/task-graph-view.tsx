"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { SubtaskNode, type SubtaskNodeData } from "./subtask-node";
import type { TaskGraphState } from "@/hooks/use-task-graph";

interface TaskGraphViewProps {
  taskGraph: TaskGraphState;
}

const nodeTypes = { subtask: SubtaskNode };

function layoutGraph(
  taskGraph: TaskGraphState,
): { nodes: Node[]; edges: Edge[] } {
  const subtasks = taskGraph.subtasks;
  const idToSubtask = new Map(subtasks.map((s) => [s.id, s]));

  // Compute layers via Kahn's algorithm (topological sort)
  const inDegree = new Map<string, number>();
  const adjList = new Map<string, string[]>();

  subtasks.forEach((s) => {
    inDegree.set(s.id, s.dependencies.length);
    s.dependencies.forEach((depId) => {
      if (!adjList.has(depId)) adjList.set(depId, []);
      adjList.get(depId)!.push(s.id);
    });
  });

  const layers: string[][] = [];
  let queue = subtasks
    .filter((s) => s.dependencies.length === 0)
    .map((s) => s.id);

  while (queue.length > 0) {
    layers.push([...queue]);
    const nextQueue: string[] = [];
    for (const id of queue) {
      for (const dependent of adjList.get(id) || []) {
        inDegree.set(dependent, inDegree.get(dependent)! - 1);
        if (inDegree.get(dependent) === 0) {
          nextQueue.push(dependent);
        }
      }
    }
    queue = nextQueue;
  }

  // Position nodes in rows by layer
  const NODE_WIDTH = 280;
  const NODE_H_GAP = 40;
  const NODE_V_GAP = 140;

  const nodes: Node[] = [];
  layers.forEach((layer, layerIndex) => {
    const totalWidth =
      layer.length * NODE_WIDTH + (layer.length - 1) * NODE_H_GAP;
    const startX = -totalWidth / 2;
    layer.forEach((id, i) => {
      const subtask = idToSubtask.get(id)!;
      nodes.push({
        id: subtask.id,
        type: "subtask",
        position: {
          x: startX + i * (NODE_WIDTH + NODE_H_GAP),
          y: layerIndex * NODE_V_GAP,
        },
        data: {
          name: subtask.name,
          description: subtask.description,
          executor: subtask.executor,
          status: subtask.status,
          result: subtask.result,
        } satisfies SubtaskNodeData,
      });
    });
  });

  // Create edges
  const edges: Edge[] = [];
  subtasks.forEach((s) => {
    s.dependencies.forEach((depId) => {
      const sourceSubtask = idToSubtask.get(depId);
      edges.push({
        id: `${depId}->${s.id}`,
        source: depId,
        target: s.id,
        animated: s.status === "in_progress" || sourceSubtask?.status === "in_progress",
        style: { stroke: "#94a3b8", strokeWidth: 2 },
      });
    });
  });

  return { nodes, edges };
}

export function TaskGraphView({
  taskGraph,
}: TaskGraphViewProps) {
  const { nodes, edges } = useMemo(
    () => layoutGraph(taskGraph),
    [taskGraph]
  );

  return (
    <div className="w-full h-full" style={{ minHeight: 400 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        colorMode="dark"
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
