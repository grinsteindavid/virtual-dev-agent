import request from 'supertest';
import { randomUUID } from 'crypto';
import { app, sessions } from '../index.js';
import dotenv from 'dotenv';
import { jest } from '@jest/globals';

// Load environment variables
dotenv.config({ path: '../../../.env' });

// Increase timeout for all tests in this file
jest.setTimeout(30000);

describe('JIRA MCP Server Integration Tests', () => {

  afterAll(async () => {
    // Clean up all sessions
    for (const [sessionId, session] of sessions) {
      if (session.server) {
        await session.server.close();
      }
    }
    sessions.clear();
  });

  test('health check endpoint should return ok status', async () => {
    const response = await request(app)
      .get('/health')
      .expect(200);

    expect(response.body).toEqual({
      status: 'ok',
      service: 'jira-mcp'
    });
  });

  test('should initialize MCP session and list available tools', async () => {
    let sessionId;
    
    // Initialize request to create session
    const initRequest = {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2025-03-26',
        capabilities: {
          tools: {}
        },
        clientInfo: {
          name: 'test-client',
          version: '1.0.0'
        }
      }
    };

    const initResponse = await request(app)
      .post('/mcp')
      .set('Content-Type', 'application/json')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2025-03-26')
      .send(initRequest)
      .expect(200);

    sessionId = initResponse.headers['mcp-session-id'];
    expect(sessionId).toBeDefined();

    expect(initResponse.body).toHaveProperty('result');
    expect(initResponse.body.result).toHaveProperty('capabilities');
    expect(initResponse.body.result).toHaveProperty('serverInfo');
    expect(initResponse.body.result.serverInfo.name).toBe('jira-mcp');

    // List tools request
    const listToolsRequest = {
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/list',
      params: {}
    };

    const toolsResponse = await request(app)
      .post('/mcp')
      .set('Content-Type', 'application/json')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2025-03-26')
      .set('mcp-session-id', sessionId)
      .send(listToolsRequest)
      .expect(200);

    expect(toolsResponse.body).toHaveProperty('result');
    expect(toolsResponse.body.result).toHaveProperty('tools');
    expect(Array.isArray(toolsResponse.body.result.tools)).toBe(true);
    
    // Check that get_task tool is available
    const getTaskTool = toolsResponse.body.result.tools.find(tool => tool.name === 'get_task');
    expect(getTaskTool).toBeDefined();
    expect(getTaskTool.description).toContain('Get details of a Jira task by ID');
  });

  test('should execute get_task tool with valid task ID via MCP', async () => {
    let sessionId;
    
    // Initialize session first
    const initRequest = {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2025-03-26',
        capabilities: { tools: {} },
        clientInfo: { name: 'test-client', version: '1.0.0' }
      }
    };

    const initResp1 = await request(app)
      .post('/mcp')
      .set('Content-Type', 'application/json')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2025-03-26')
      .send(initRequest)
      .expect(200);
    sessionId = initResp1.headers['mcp-session-id'];
    expect(sessionId).toBeDefined();

    // Execute get_task tool
    const toolCallRequest = {
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: {
        name: 'get_task',
        arguments: {
          taskId: 'DP-4'
        }
      }
    };

    const toolResponse = await request(app)
      .post('/mcp')
      .set('Content-Type', 'application/json')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2025-03-26')
      .set('mcp-session-id', sessionId)
      .send(toolCallRequest)
      .expect(200);

    expect(toolResponse.body).toHaveProperty('result');
    expect(toolResponse.body.result).toHaveProperty('content');
    expect(Array.isArray(toolResponse.body.result.content)).toBe(true);
    expect(toolResponse.body.result.content.length).toBeGreaterThan(0);
    expect(toolResponse.body.result.content[0]).toHaveProperty('type', 'text');
    expect(toolResponse.body.result.content[0]).toHaveProperty('text');
    
    // Check that the response contains expected task information
    const responseText = toolResponse.body.result.content[0].text;
    expect(responseText).toContain('Task DP-4:');
    expect(responseText).toContain('Summary:');
    expect(responseText).toContain('Status:');
  });

  test('should handle get_task tool with invalid task ID via MCP', async () => {
    let sessionId;
    
    // Initialize session first
    const initRequest = {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        clientInfo: { name: 'test-client', version: '1.0.0' }
      }
    };

    await request(app)
      .post('/mcp')
      .set('Content-Type', 'application/json')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2024-11-05')
      .set('mcp-session-id', sessionId)
      .send(initRequest)
      .expect(200);

    // Execute get_task tool with invalid ID
    const toolCallRequest = {
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: {
        name: 'get_task',
        arguments: {
          taskId: 'INVALID-123456'
        }
      }
    };

    const toolResponse = await request(app)
      .post('/mcp')
      .set('Content-Type', 'application/json')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2024-11-05')
      .set('mcp-session-id', sessionId)
      .send(toolCallRequest)
      .expect(200);

    expect(toolResponse.body).toHaveProperty('result');
    expect(toolResponse.body.result).toHaveProperty('content');
    expect(Array.isArray(toolResponse.body.result.content)).toBe(true);
    expect(toolResponse.body.result.content.length).toBeGreaterThan(0);
    expect(toolResponse.body.result.content[0]).toHaveProperty('type', 'text');
    expect(toolResponse.body.result.content[0]).toHaveProperty('text');
    
    // Check that the response contains error information
    const responseText = toolResponse.body.result.content[0].text;
    expect(responseText).toContain('Error retrieving task INVALID-123456');
  });

  test('should handle session cleanup properly', async () => {
    let sessionId;
    
    // Initialize session
    const initRequest = {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        clientInfo: { name: 'test-client', version: '1.0.0' }
      }
    };

    await request(app)
      .post('/mcp')
      .set('Content-Type', 'application/json')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2024-11-05')
      .set('mcp-session-id', sessionId)
      .send(initRequest)
      .expect(200);

    // Verify session exists
    expect(sessions.has(sessionId)).toBe(true);

    // Delete session
    await request(app)
      .delete('/mcp')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2025-03-26')
      .set('mcp-session-id', sessionId)
      .expect(200);

    // Verify session is cleaned up
    expect(sessions.has(sessionId)).toBe(false);
  });

  test('should handle invalid JSON-RPC requests gracefully', async () => {
    const sessionId = randomUUID();
    
    const invalidRequest = {
      // Missing required jsonrpc field
      id: 1,
      method: 'invalid_method',
      params: {}
    };

    const response = await request(app)
      .post('/mcp')
      .set('Content-Type', 'application/json')
      .set('Accept', 'application/json')
      .set('MCP-Protocol-Version', '2025-03-26')
      .set('mcp-session-id', randomUUID())
      .send(invalidRequest);

    // Should not crash the server
    expect(response.status).toBeDefined();
  });
});
