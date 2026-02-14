"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send } from "lucide-react";

interface ChatInterfaceProps {
  categoryId: number;
}

export function ChatInterface({ categoryId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState("");
  const ws = useRef<WebSocket | null>(null);

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
        if (!cancelled) {
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
  }, [categoryId]);

  const sendMessage = () => {
    if (!input.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;

    // Add user message to UI
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    
    // Send to backend
    ws.current.send(input);
    
    setInput("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full border rounded-lg bg-white shadow-sm overflow-hidden">
      <div className="p-4 border-b bg-gray-50">
        <h3 className="font-semibold">Chat</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-20">
            Start a conversation...
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div 
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === "user" 
                    ? "bg-blue-600 text-white" 
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="p-4 border-t bg-gray-50 flex gap-2">
        <Input 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyDown={handleKeyPress}
          placeholder="Type your message..."
          className="flex-1"
        />
        <Button onClick={sendMessage} size="icon">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
