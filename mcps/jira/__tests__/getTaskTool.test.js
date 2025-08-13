import { getTaskTool } from '../toolHandlers.js';
import dotenv from 'dotenv';
import { jest } from '@jest/globals';

// Ensure environment variables are loaded
dotenv.config({ path: '../../../.env' });

// Increase timeout for all tests in this file
jest.setTimeout(30000);

describe('getTaskTool', () => {
  // Test the actual functionality with a real Jira task ID
  test('should retrieve task details for a valid task ID', async () => {
    const testTaskId = 'DP-4';
    const result = await getTaskTool.handler({ taskId: testTaskId });
    
    // Check the structure of the response
    expect(result).toHaveProperty('content');
    expect(Array.isArray(result.content)).toBe(true);
    expect(result.content.length).toBeGreaterThan(0);
    expect(result.content[0]).toHaveProperty('type', 'text');
    expect(result.content[0]).toHaveProperty('text');
    
    // Check that the response contains expected information
    const responseText = result.content[0].text;
    expect(responseText).toContain(`Task ${testTaskId}:`);
    expect(responseText).toContain('Summary:');
    expect(responseText).toContain('Status:');
    expect(responseText).toContain('Assignee:');
    expect(responseText).toContain('Priority:');
    expect(responseText).toContain('Description:');
  });

  // Test error handling with an invalid task ID
  test('should handle errors for an invalid task ID', async () => {
    const invalidTaskId = 'INVALID-123456';
    
    const result = await getTaskTool.handler({ taskId: invalidTaskId });
    
    // Check the structure of the error response
    expect(result).toHaveProperty('content');
    expect(Array.isArray(result.content)).toBe(true);
    expect(result.content.length).toBeGreaterThan(0);
    expect(result.content[0]).toHaveProperty('type', 'text');
    expect(result.content[0]).toHaveProperty('text');
    
    // Check that the response contains error information
    const responseText = result.content[0].text;
    expect(responseText).toContain(`Error retrieving task ${invalidTaskId}`);
  });
});
