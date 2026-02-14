"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createMCPServer, MCPServerCreate } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useQuery } from "@tanstack/react-query";
import { suggestServers } from "@/lib/api";
import { Badge } from "lucide-react"; // Wait, badge is from shadcn. I need to install it or use something else. I'll use simple div.

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  url: z.string().url("Must be a valid URL"),
});

interface AddServerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  categoryId: number;
  categoryName: string;
}

export function AddServerDialog({ open, onOpenChange, categoryId, categoryName }: AddServerDialogProps) {
  const queryClient = useQueryClient();
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      url: "",
    },
  });

  // Fetch suggestions
  const { data: suggestions } = useQuery({
    queryKey: ["suggestions", categoryName],
    queryFn: () => suggestServers(categoryName),
    enabled: open && !!categoryName,
  });

  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof formSchema>) => 
      createMCPServer({ ...values, category_id: categoryId, type: "sse" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      onOpenChange(false);
      form.reset();
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    mutation.mutate(values);
  }

  const fillSuggestion = (suggestion: any) => {
    form.setValue("name", suggestion.name);
    form.setValue("url", suggestion.url);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add MCP Server</DialogTitle>
          <DialogDescription>
            Connect a new MCP server to this category.
          </DialogDescription>
        </DialogHeader>
        
        {suggestions && suggestions.length > 0 && (
          <div className="mb-4 space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Suggested Servers:</h4>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s, i) => (
                <Button 
                    key={i} 
                    variant="outline" 
                    size="sm" 
                    onClick={() => fillSuggestion(s)}
                    className="h-auto py-1 px-2 text-xs flex flex-col items-start gap-0.5"
                >
                    <span className="font-semibold">{s.name}</span>
                    <span className="text-[10px] text-muted-foreground truncate max-w-[150px]">{s.url}</span>
                </Button>
              ))}
            </div>
          </div>
        )}

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. GitHub Agent" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Server URL</FormLabel>
                  <FormControl>
                    <Input placeholder="https://..." {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Adding..." : "Add Server"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
