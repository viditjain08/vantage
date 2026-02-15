"use client";

import { useState, useEffect, useRef, useCallback, useImperativeHandle, forwardRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Send, Sparkles, Loader2, User, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { enhancePrompt } from "@/lib/api";
import type { ServerMessage, Subtask, SubtaskStatus } from "@/lib/ws-types";
import type { TaskGraphState } from "@/hooks/use-task-graph";

interface ChatInterfaceProps {
  categoryId: number;
  onGraphCreated: (taskId: string, userMessage: string, subtasks: Subtask[]) => void;
  onStatusUpdate: (subtaskId: string, status: SubtaskStatus, result: string | null, prompt: string | null) => void;
  taskGraph: TaskGraphState | null;
}

export interface ChatInterfaceHandle {
  sendUserSubtaskOutput: (subtaskId: string, output: string) => void;
  sendStartTask: (taskId: string) => void;
}

function UserSubtaskCard({
  subtask,
  onSubmit,
}: {
  subtask: Subtask;
  onSubmit: (subtaskId: string, output: string) => void;
}) {
  const [output, setOutput] = useState("");
  const [copied, setCopied] = useState(false);

  const handleCopyPrompt = async () => {
    if (subtask.prompt) {
      await navigator.clipboard.writeText(subtask.prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSubmit = () => {
    if (output.trim()) {
      onSubmit(subtask.id, output);
      setOutput("");
    }
  };

  return (
    <div className="flex justify-start">
      <div className="max-w-[90%] w-full rounded-lg border-2 border-yellow-400 bg-yellow-50 p-4 space-y-3">
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-purple-500 shrink-0" />
          <span className="font-semibold text-sm text-gray-800">Action Required: {subtask.name}</span>
          <Loader2 className="h-4 w-4 animate-spin text-yellow-500 shrink-0 ml-auto" />
        </div>

        <p className="text-sm text-gray-600">{subtask.description}</p>

        {subtask.prompt && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Prompt for your local LLM</span>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs gap-1"
                onClick={handleCopyPrompt}
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3 text-green-500" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" />
                    Copy prompt
                  </>
                )}
              </Button>
            </div>
            <pre className="text-xs bg-gray-800 text-gray-100 p-3 rounded-md overflow-x-auto whitespace-pre-wrap max-h-[200px] overflow-y-auto">
              {subtask.prompt}
            </pre>
          </div>
        )}

        <div className="space-y-1.5">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Paste your output</span>
          <Textarea
            value={output}
            onChange={(e) => setOutput(e.target.value)}
            placeholder="Paste the output from your local LLM or provide your response here..."
            className="min-h-[100px] text-sm bg-white"
          />
        </div>

        <div className="flex justify-end">
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={!output.trim()}
            className="gap-1"
          >
            <Send className="h-3 w-3" />
            Submit Output
          </Button>
        </div>
      </div>
    </div>
  );
}

export const ChatInterface = forwardRef<ChatInterfaceHandle, ChatInterfaceProps>(
  function ChatInterface({ categoryId, onGraphCreated, onStatusUpdate, taskGraph }, ref) {
    const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
    const [input, setInput] = useState("");
    const [isEnhancing, setIsEnhancing] = useState(false);
    const ws = useRef<WebSocket | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      let reconnectTimeout: NodeJS.Timeout;
      let cancelled = false;
      let socket: WebSocket | null = null;

      function connect() {
        const wsUrl = process.env.NEXT_PUBLIC_API_URL
          ? process.env.NEXT_PUBLIC_API_URL.replace("http", "ws").replace("/api/v1", "") + `/ws/chat/${categoryId}`
          : `ws://localhost:8000/ws/chat/${categoryId}`;

        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
          if (cancelled) {
            socket?.close();
            return;
          }
          ws.current = socket;
          console.log("WebSocket connected");
        };

        socket.onmessage = (event) => {
          if (cancelled) return;

          try {
            const msg: ServerMessage = JSON.parse(event.data);

            switch (msg.type) {
              case "chat_response":
                setMessages((prev) => [...prev, { role: "assistant", content: msg.content }]);
                break;
              case "task_graph_created":
                onGraphCreated(msg.task_id, msg.user_message, msg.subtasks);
                break;
              case "subtask_status_update":
                onStatusUpdate(msg.subtask_id, msg.status, msg.result, msg.prompt ?? null);
                break;
              case "task_completed":
                setMessages((prev) => [...prev, { role: "assistant", content: msg.summary }]);
                break;
              case "mcp_connection_status": {
                const failed = msg.servers.filter((s) => !s.connected);
                if (failed.length > 0) {
                  const lines = failed.map(
                    (s) => `- **${s.name}**: ${s.error || "Connection failed"}`
                  );
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content: `**Failed to connect to MCP server(s):**\n${lines.join("\n")}\n\nSubtasks requiring these servers will need manual input. Check server URL and credentials.`,
                    },
                  ]);
                }
                break;
              }
              case "error":
                setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${msg.content}` }]);
                break;
            }
          } catch {
            setMessages((prev) => [...prev, { role: "assistant", content: event.data }]);
          }
        };

        socket.onerror = () => {};

        socket.onclose = (event) => {
          if (cancelled) return;
          console.log(`WebSocket closed: code=${event.code} reason=${event.reason}`);
          ws.current = null;
          reconnectTimeout = setTimeout(connect, 3000);
        };
      }

      connect();

      return () => {
        cancelled = true;
        clearTimeout(reconnectTimeout);
        socket?.close();
        ws.current = null;
      };
    }, [categoryId, onGraphCreated, onStatusUpdate]);

    // Auto-scroll to bottom when new messages arrive or subtask status changes
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, taskGraph]);

    const sendUserSubtaskOutput = useCallback((subtaskId: string, output: string) => {
      if (!ws.current || !taskGraph) return;
      ws.current.send(JSON.stringify({
        type: "user_subtask_output",
        task_id: taskGraph.taskId,
        subtask_id: subtaskId,
        output,
      }));
    }, [taskGraph]);

    const sendStartTask = useCallback((taskId: string) => {
      if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;
      ws.current.send(JSON.stringify({
        type: "start_task",
        task_id: taskId,
      }));
    }, []);

    useImperativeHandle(ref, () => ({
      sendUserSubtaskOutput,
      sendStartTask,
    }), [sendUserSubtaskOutput, sendStartTask]);

    const sendMessage = () => {
      if (!input.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;

      setMessages((prev) => [...prev, { role: "user", content: input }]);

      ws.current.send(JSON.stringify({ type: "chat_message", content: input }));

      setInput("");
    };

    const handleEnhance = async () => {
      if (!input.trim() || isEnhancing) return;
      setIsEnhancing(true);
      try {
        const enhanced = await enhancePrompt(categoryId, input);
        setInput(enhanced);
      } catch (err) {
        console.error("Failed to enhance prompt:", err);
      } finally {
        setIsEnhancing(false);
      }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    };

    // Get user subtasks that are currently awaiting input
    const activeUserSubtasks = taskGraph?.subtasks.filter(
      (s) => s.executor === "user" && s.status === "in_progress"
    ) ?? [];

    return (
      <div className="flex flex-col h-full border rounded-lg bg-white shadow-sm overflow-hidden">
        <div className="p-4 border-b bg-gray-50">
          <h3 className="font-semibold">Chat</h3>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && activeUserSubtasks.length === 0 ? (
            <div className="text-center text-gray-400 mt-20">
              Start a conversation...
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-4 py-2 ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div className="prose prose-sm max-w-none prose-gray prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-pre:my-2 prose-code:before:content-none prose-code:after:content-none prose-code:bg-gray-200 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-gray-800 prose-pre:bg-gray-800 prose-pre:text-gray-100 prose-a:text-blue-600">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}

              {/* User subtask input cards rendered inline in chat */}
              {activeUserSubtasks.map((subtask) => (
                <UserSubtaskCard
                  key={subtask.id}
                  subtask={subtask}
                  onSubmit={sendUserSubtaskOutput}
                />
              ))}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t bg-gray-50 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1"
          />
          <Button
            onClick={handleEnhance}
            size="icon"
            variant="outline"
            disabled={!input.trim() || isEnhancing}
            title="Enhance prompt"
          >
            {isEnhancing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          </Button>
          <Button onClick={sendMessage} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    );
  }
);
