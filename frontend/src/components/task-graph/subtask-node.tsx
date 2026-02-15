"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { User, Bot, Loader2, CheckCircle2, XCircle } from "lucide-react";
import type { SubtaskStatus, SubtaskExecutor } from "@/lib/ws-types";

export interface SubtaskNodeData {
  name: string;
  description: string;
  executor: SubtaskExecutor;
  status: SubtaskStatus;
  result: string | null;
  [key: string]: unknown;
}

const STATUS_BORDER_COLORS: Record<SubtaskStatus, string> = {
  pending: "border-white",
  in_progress: "border-yellow-400",
  succeeded: "border-green-500",
  failed: "border-red-500",
};

const STATUS_BG_COLORS: Record<SubtaskStatus, string> = {
  pending: "bg-gray-900",
  in_progress: "bg-gray-900",
  succeeded: "bg-gray-900",
  failed: "bg-gray-900",
};

export function SubtaskNode({ data }: NodeProps) {
  const nodeData = data as SubtaskNodeData;
  const { name, description, executor, status, result } = nodeData;

  return (
    <div
      className={`rounded-lg shadow-md border-2 ${STATUS_BORDER_COLORS[status]} ${STATUS_BG_COLORS[status]} p-3 min-w-[220px] max-w-[300px]`}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />

      <div className="flex items-center gap-2 mb-1">
        {executor === "system" ? (
          <Bot className="h-4 w-4 text-blue-400 shrink-0" />
        ) : (
          <User className="h-4 w-4 text-purple-400 shrink-0" />
        )}
        <span className="font-semibold text-sm text-gray-100 truncate flex-1">{name}</span>
        {status === "in_progress" && (
          <Loader2 className="h-4 w-4 animate-spin text-yellow-400 shrink-0" />
        )}
        {status === "succeeded" && (
          <CheckCircle2 className="h-4 w-4 text-green-400 shrink-0" />
        )}
        {status === "failed" && (
          <XCircle className="h-4 w-4 text-red-400 shrink-0" />
        )}
      </div>

      <p className="text-xs text-gray-400 mb-2">{description}</p>

      {/* Show result if completed */}
      {result && (status === "succeeded" || status === "failed") && (
        <div
          className={`text-xs p-2 rounded mt-1 max-h-[80px] overflow-y-auto ${
            status === "succeeded"
              ? "bg-green-900/30 text-green-300"
              : "bg-red-900/30 text-red-300"
          }`}
        >
          {result}
        </div>
      )}

      {/* User subtask input is now handled in the chat interface */}
      {executor === "user" && status === "in_progress" && (
        <div className="text-xs text-yellow-400 mt-2 italic">
          Waiting for input in chat...
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
    </div>
  );
}
