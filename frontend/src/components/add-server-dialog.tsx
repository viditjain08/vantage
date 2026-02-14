"use client";

import { useState } from "react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { createMCPServer, suggestServers, CatalogEntry, ResourceConfigField } from "@/lib/api";
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
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
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

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  url: z.string(),
});

interface AddServerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  categoryId: number;
  categoryName: string;
}

const PROVIDER_MAP: Record<string, string> = {
  aws: "aws",
  azure: "azure",
  gcp: "gcp",
  kubernetes: "kubernetes",
};

export function AddServerDialog({ open, onOpenChange, categoryId, categoryName }: AddServerDialogProps) {
  const queryClient = useQueryClient();
  const [configSchema, setConfigSchema] = useState<ResourceConfigField[]>([]);
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [serverType, setServerType] = useState<string>("sse");
  const [stdioConfig, setStdioConfig] = useState<{ command: string; args: string[] } | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      url: "",
    },
  });

  const { data: suggestions } = useQuery({
    queryKey: ["suggestions", categoryId],
    queryFn: () => suggestServers(categoryId),
    enabled: open && !!categoryId,
  });

  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof formSchema>) => {
      const hasConfig = Object.keys(configValues).some((k) => configValues[k]);
      let resource_config: Record<string, any> | undefined;

      if (serverType === "stdio" && stdioConfig) {
        resource_config = {
          command: stdioConfig.command,
          args: stdioConfig.args,
          ...(hasConfig ? { env: configValues } : {}),
        };
      } else if (hasConfig) {
        resource_config = { provider: selectedProvider, ...configValues };
      }

      return createMCPServer({
        ...values,
        category_id: categoryId,
        type: serverType,
        resource_config,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      onOpenChange(false);
      form.reset();
      setConfigSchema([]);
      setConfigValues({});
      setSelectedProvider("");
      setServerType("sse");
      setStdioConfig(null);
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    mutation.mutate(values);
  }

  const fillSuggestion = (suggestion: CatalogEntry) => {
    form.setValue("name", suggestion.name);
    form.setValue("url", suggestion.url || "");
    setConfigSchema(suggestion.config_schema || []);
    setConfigValues({});
    setSelectedProvider(PROVIDER_MAP[suggestion.name.toLowerCase()] || "");
    setServerType(suggestion.type || "sse");
    setStdioConfig(suggestion.stdio_config || null);
  };

  const updateConfigValue = (fieldName: string, value: string) => {
    setConfigValues((prev) => ({ ...prev, [fieldName]: value }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[85vh] overflow-y-auto">
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
                  <span className="text-[10px] text-muted-foreground truncate max-w-[150px]">{s.type === "stdio" ? "stdio" : s.url}</span>
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
            {serverType === "stdio" ? (
              <div className="rounded-md border p-3 bg-muted/50 space-y-1">
                <p className="text-sm font-medium">Stdio Server</p>
                {stdioConfig && (
                  <p className="text-xs text-muted-foreground font-mono">
                    {stdioConfig.command} {stdioConfig.args.join(" ")}
                  </p>
                )}
              </div>
            ) : (
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
            )}

            {configSchema.length > 0 && (
              <div className="space-y-3 border-t pt-3">
                <h4 className="text-sm font-medium">Resource Configuration</h4>
                {configSchema.map((field) => (
                  <div key={field.name} className="space-y-1">
                    <Label className="text-sm">
                      {field.label}
                      {field.required && <span className="text-destructive"> *</span>}
                    </Label>
                    {field.type === "textarea" ? (
                      <Textarea
                        placeholder={field.placeholder}
                        value={configValues[field.name] || ""}
                        onChange={(e) => updateConfigValue(field.name, e.target.value)}
                        className="min-h-[80px] text-sm"
                      />
                    ) : (
                      <Input
                        type={field.type === "password" ? "password" : "text"}
                        placeholder={field.placeholder}
                        value={configValues[field.name] || ""}
                        onChange={(e) => updateConfigValue(field.name, e.target.value)}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}

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
