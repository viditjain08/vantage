import { useReducer, useCallback } from "react";
import type { Subtask, SubtaskStatus } from "@/lib/ws-types";

export interface TaskGraphState {
  taskId: string;
  userMessage: string;
  subtasks: Subtask[];
}

type Action =
  | {
      type: "GRAPH_CREATED";
      taskId: string;
      userMessage: string;
      subtasks: Subtask[];
    }
  | {
      type: "STATUS_UPDATE";
      subtaskId: string;
      status: SubtaskStatus;
      result: string | null;
    }
  | { type: "CLEAR" };

function reducer(
  state: TaskGraphState | null,
  action: Action
): TaskGraphState | null {
  switch (action.type) {
    case "GRAPH_CREATED":
      return {
        taskId: action.taskId,
        userMessage: action.userMessage,
        subtasks: action.subtasks,
      };
    case "STATUS_UPDATE":
      if (!state) return null;
      return {
        ...state,
        subtasks: state.subtasks.map((s) =>
          s.id === action.subtaskId
            ? { ...s, status: action.status, result: action.result }
            : s
        ),
      };
    case "CLEAR":
      return null;
    default:
      return state;
  }
}

export function useTaskGraph() {
  const [taskGraph, dispatch] = useReducer(reducer, null);

  const handleGraphCreated = useCallback(
    (taskId: string, userMessage: string, subtasks: Subtask[]) => {
      dispatch({ type: "GRAPH_CREATED", taskId, userMessage, subtasks });
    },
    []
  );

  const handleStatusUpdate = useCallback(
    (subtaskId: string, status: SubtaskStatus, result: string | null) => {
      dispatch({ type: "STATUS_UPDATE", subtaskId, status, result });
    },
    []
  );

  const clearGraph = useCallback(() => dispatch({ type: "CLEAR" }), []);

  return { taskGraph, handleGraphCreated, handleStatusUpdate, clearGraph };
}
