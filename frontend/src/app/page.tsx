"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Sidebar } from "@/components/sidebar";
import { getCategories } from "@/lib/api";
import { CreateCategoryDialog } from "@/components/create-category-dialog";
import { MCPServerList } from "@/components/mcp-server-list";
import { ChatInterface, type ChatInterfaceHandle } from "@/components/chat-interface";
import { TaskGraphView } from "@/components/task-graph/task-graph-view";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useTaskGraph } from "@/hooks/use-task-graph";

export default function Home() {
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | undefined>(undefined);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const chatRef = useRef<ChatInterfaceHandle>(null);

  const { data: categories = [], isLoading, error } = useQuery({
    queryKey: ["categories"],
    queryFn: getCategories,
  });

  const { taskGraph, handleGraphCreated, handleStatusUpdate, clearGraph } = useTaskGraph();

  const selectedCategory = categories.find(c => c.id === selectedCategoryId);

  // Auto-select first category if none selected and available
  useEffect(() => {
    if (!selectedCategoryId && categories.length > 0) {
      setSelectedCategoryId(categories[0].id);
    }
  }, [categories, selectedCategoryId]);

  // Clear task graph when switching categories
  useEffect(() => {
    clearGraph();
  }, [selectedCategoryId, clearGraph]);

  const handleUserSubtaskSubmit = useCallback((subtaskId: string, output: string) => {
    chatRef.current?.sendUserSubtaskOutput(subtaskId, output);
  }, []);

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden">
      <Sidebar
        categories={categories}
        onSelectCategory={setSelectedCategoryId}
        selectedCategoryId={selectedCategoryId}
        onNewCategory={() => setIsCreateDialogOpen(true)}
        isLoading={isLoading}
        error={error}
      />

      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {selectedCategory ? (
          <div className="flex-1 overflow-y-auto p-8 space-y-6">
            <div className="max-w-4xl mx-auto w-full space-y-6">
                <div>
                   <h1 className="text-3xl font-bold">{selectedCategory.name}</h1>
                   <p className="text-muted-foreground text-sm mt-1">Managed Context & Tools</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                        {taskGraph ? (
                          <>
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="icon-xs" onClick={clearGraph}>
                                <ArrowLeft className="h-4 w-4" />
                              </Button>
                              <h3 className="font-semibold text-sm">Task Graph</h3>
                            </div>
                            <div className="h-[600px] border rounded-lg overflow-hidden">
                              <TaskGraphView
                                taskGraph={taskGraph}
                                onUserSubtaskSubmit={handleUserSubtaskSubmit}
                              />
                            </div>
                          </>
                        ) : (
                          <>
                            <MCPServerList
                              categoryId={selectedCategory.id}
                              categoryName={selectedCategory.name}
                              servers={selectedCategory.mcp_servers || []}
                            />

                            <div className="p-4 border rounded-lg bg-muted/30">
                              <h3 className="font-semibold mb-2 text-sm">System Prompt</h3>
                              <div className="bg-muted p-3 rounded text-xs font-mono whitespace-pre-wrap max-h-[200px] overflow-y-auto">
                                {selectedCategory.system_prompt}
                              </div>
                            </div>
                          </>
                        )}
                    </div>

                    <div className="h-[700px]">
                         <ChatInterface
                           ref={chatRef}
                           categoryId={selectedCategory.id}
                           onGraphCreated={handleGraphCreated}
                           onStatusUpdate={handleStatusUpdate}
                           taskGraph={taskGraph}
                         />
                    </div>
                </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4 text-muted-foreground">
            <h1 className="text-2xl font-bold text-foreground">Welcome to Vantage</h1>
            <p>Select a category from the sidebar or create a new one to get started.</p>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              Create Category
            </Button>
          </div>
        )}
      </main>

      <CreateCategoryDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
      />
    </div>
  );
}
