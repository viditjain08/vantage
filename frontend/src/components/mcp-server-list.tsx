"use client";

import { useState } from "react";
import { MCPServer, deleteMCPServer } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Plus, Trash2, Server } from "lucide-react";
import { AddServerDialog } from "@/components/add-server-dialog";
import { useMutation, useQueryClient } from "@tanstack/react-query";

interface MCPServerListProps {
  categoryId: number;
  categoryName: string;
  servers: MCPServer[];
}

export function MCPServerList({ categoryId, categoryName, servers }: MCPServerListProps) {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: deleteMCPServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  return (
    <div className="space-y-4 border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Server className="h-5 w-5" />
          MCP Servers
        </h3>
        <Button size="sm" onClick={() => setIsAddDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Server
        </Button>
      </div>

      {servers.length === 0 ? (
        <div className="text-center text-gray-500 py-4 text-sm">
          No servers connected. Add one to enable tools.
        </div>
      ) : (
        <div className="space-y-2">
          {servers.map((server) => (
            <div 
              key={server.id} 
              className="flex items-center justify-between p-3 border rounded-md bg-gray-50"
            >
              <div>
                <div className="font-medium">{server.name}</div>
                <div className="text-xs text-gray-500 truncate max-w-[300px]">{server.url}</div>
              </div>
              <Button 
                variant="ghost" 
                size="icon" 
                className="text-red-500 hover:text-red-700 hover:bg-red-50"
                onClick={() => deleteMutation.mutate(server.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      <AddServerDialog 
        open={isAddDialogOpen} 
        onOpenChange={setIsAddDialogOpen} 
        categoryId={categoryId}
        categoryName={categoryName}
      />
    </div>
  );
}
