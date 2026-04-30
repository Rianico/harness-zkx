# MCP Server Patterns

Model Context Protocol (MCP) server implementation patterns for Node/TypeScript SDK.

## Core Concepts

| Concept | Purpose | Example |
|---------|---------|---------|
| **Tools** | Actions the model can invoke | Search, run command, fetch data |
| **Resources** | Read-only data the model can fetch | File contents, API responses, database rows |
| **Prompts** | Reusable, parameterized templates | "Analyze this file for X" |
| **Transport** | Communication method | stdio (local) or Streamable HTTP (remote) |

## Tool Registration

The SDK API has evolved. Check Context7 (query "MCP") or [official docs](https://modelcontextprotocol.io) for current method signatures.

### Example Pattern (verify against current SDK)

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({ name: "my-server", version: "1.0.0" });

// Tool registration pattern varies by SDK version
// Some use positional args, others use object params
server.tool(
  "search",
  "Search for documents matching a query",
  { query: z.string().describe("Search query") },
  async (params) => {
    const results = await searchDocs(params.query);
    return { content: [{ type: "text", text: JSON.stringify(results) }] };
  }
);
```

### Schema-First Design

Always define input schemas with Zod or the SDK's preferred format:

```typescript
const SearchSchema = z.object({
  query: z.string().describe("Search query"),
  limit: z.number().optional().default(10).describe("Max results"),
  filters: z.record(z.string()).optional().describe("Optional filters"),
});
```

## Resource Registration

Resources provide read-only data. Handlers typically receive a `uri` argument.

```typescript
server.resource(
  "file",
  "file:///{path}",
  async (uri, params) => {
    const content = await readFile(params.path);
    return {
      contents: [{
        uri: uri.href,
        text: content,
        mimeType: "text/plain",
      }],
    };
  }
);
```

## Prompt Registration

Prompts are reusable templates surfaced to the client:

```typescript
server.prompt(
  "analyze-code",
  "Analyze code for potential issues",
  { file: z.string().describe("File path to analyze") },
  async (params) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Analyze the code in ${params.file} for potential bugs, security issues, and improvements.`,
      },
    }],
  })
);
```

## Transport Selection

| Transport | Use Case | Clients |
|-----------|----------|---------|
| **stdio** | Local development, Claude Desktop | Claude Desktop, local CLI tools |
| **Streamable HTTP** | Remote access, cloud deployment | Cursor, cloud integrations, web clients |
| **HTTP/SSE (legacy)** | Backward compatibility only | Older clients |

### stdio Setup

```typescript
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Streamable HTTP Setup

For remote access, use the Streamable HTTP transport (single endpoint per current spec):

```typescript
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamable-http.js";

const transport = new StreamableHTTPServerTransport();
// Mount on your HTTP server at a single endpoint
```

**Architecture tip:** Keep tool/resource logic independent of transport. Plug in transport in the entrypoint only.

## Error Handling

Return structured errors the model can interpret:

```typescript
server.tool("fetch-data", async (params) => {
  try {
    const data = await fetchData(params.id);
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  } catch (error) {
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          error: true,
          message: error.message,
          retryable: error.isRetryable ?? false,
        }),
      }],
      isError: true,
    };
  }
});
```

## Best Practices

### Schema First
Define input schemas for every tool. Document parameters and return shapes.

### Structured Errors
Return errors the model can interpret and act on. Avoid raw stack traces.

### Idempotency
Prefer idempotent tools where retries are safe. Mark non-idempotent tools clearly.

### Rate and Cost
For tools calling external APIs, document rate limits and cost in the description.

### Versioning
Pin SDK version in `package.json`. Check release notes when upgrading—APIs change.

### Transport Independence
Keep server logic (tools + resources) separate from transport setup.

## Official SDKs

| Language | Package |
|----------|---------|
| TypeScript/JavaScript | `@modelcontextprotocol/sdk` (npm) |
| Go | `modelcontextprotocol/go-sdk` |
| C# | Official .NET SDK |
| Python | Official Python SDK |

## Quick Reference

```bash
# Install
npm install @modelcontextprotocol/sdk zod

# Check latest docs
# Use Context7 with library "MCP" or visit modelcontextprotocol.io
```
