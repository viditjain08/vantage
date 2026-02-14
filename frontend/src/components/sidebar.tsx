"use client";

import { useQuery } from "@tanstack/react-query";
import { getCategories, Category } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Plus, MessageSquare, Database } from "lucide-react";
import Link from "next/link";

interface SidebarProps {
  categories: Category[];
  onSelectCategory: (id: number) => void;
  selectedCategoryId?: number;
  onNewCategory: () => void;
  isLoading: boolean;
  error: any;
}

export function Sidebar({ categories, onSelectCategory, selectedCategoryId, onNewCategory, isLoading, error }: SidebarProps) {
  return (
    <div className="w-64 border-r h-full bg-gray-50 flex flex-col">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Database className="h-6 w-6" />
          Vantage
        </h1>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-gray-500">Categories</h2>
          <Button variant="ghost" size="icon" onClick={onNewCategory} className="h-6 w-6">
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {isLoading && <div className="text-sm text-gray-400">Loading...</div>}
        {error && <div className="text-sm text-red-500">Error loading categories</div>}

        <div className="space-y-1">
            {categories?.map((cat) => (
            <Button
                key={cat.id}
                variant={selectedCategoryId === cat.id ? "secondary" : "ghost"}
                className="w-full justify-start font-normal"
                onClick={() => onSelectCategory(cat.id)}
            >
                <MessageSquare className="mr-2 h-4 w-4" />
                {cat.name}
            </Button>
            ))}
        </div>
      </div>
    </div>
  );
}
