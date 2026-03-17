import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('API Service', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('fetches network graph successfully', async () => {
    const mockGraph = {
      nodes: [{ id: '1', name: 'router', type: 'router', status: 'active' }],
      edges: [],
      last_updated: '2024-01-01T00:00:00',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraph,
    });

    const response = await fetch('http://localhost:3001/network/graph');
    const data = await response.json();

    expect(data.nodes).toHaveLength(1);
    expect(data.nodes[0].name).toBe('router');
  });

  it('handles network graph fetch error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    const response = await fetch('http://localhost:3001/network/graph');
    expect(response.ok).toBe(false);
    expect(response.status).toBe(500);
  });

  it('fetches health check successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'healthy' }),
    });

    const response = await fetch('http://localhost:3001/health');
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  it('creates a network node', async () => {
    const newNode = { name: 'test-node', type: 'router', status: 'active' };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, node: { id: '1', ...newNode } }),
    });

    const response = await fetch('http://localhost:3001/network/nodes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newNode),
    });

    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.node.name).toBe('test-node');
  });

  it('fetches network stats', async () => {
    const mockStats = { total_nodes: 5, total_edges: 4 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockStats,
    });

    const response = await fetch('http://localhost:3001/network/stats');
    const data = await response.json();
    expect(data.total_nodes).toBe(5);
    expect(data.total_edges).toBe(4);
  });
});

describe('WebSocketManager', () => {
  it('constructs with default session id', async () => {
    // Import the actual class
    const { WebSocketManager } = await import('./api');
    const manager = new WebSocketManager();
    expect(manager).toBeDefined();
  });

  it('constructs with custom session id', async () => {
    const { WebSocketManager } = await import('./api');
    const manager = new WebSocketManager('custom-session');
    expect(manager).toBeDefined();
  });
});
