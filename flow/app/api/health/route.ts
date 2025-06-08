import { NextRequest, NextResponse } from 'next/server';

// Mock health data - in production this would check actual services
const getSystemHealth = () => {
  const uptime = process.uptime();
  const memoryUsage = process.memoryUsage();
  
  return {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: {
      seconds: Math.floor(uptime),
      formatted: `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m ${Math.floor(uptime % 60)}s`
    },
    services: {
      langflow: {
        status: 'connected',
        url: process.env.LANGFLOW_BASE_URL || 'http://localhost:7860',
        last_check: new Date().toISOString(),
        response_time: Math.floor(Math.random() * 100) + 50 // Mock response time
      },
      redis: {
        status: 'connected',
        url: process.env.REDIS_URL || 'redis://localhost:6379',
        last_check: new Date().toISOString(),
        response_time: Math.floor(Math.random() * 20) + 5
      },
      database: {
        status: 'healthy',
        type: 'sqlite',
        last_check: new Date().toISOString(),
        response_time: Math.floor(Math.random() * 30) + 10
      }
    },
    agents: {
      classifier: {
        status: 'active',
        last_execution: new Date(Date.now() - Math.random() * 3600000).toISOString(),
        success_rate: 0.95,
        avg_response_time: 1250
      },
      email: {
        status: 'active',
        last_execution: new Date(Date.now() - Math.random() * 1800000).toISOString(),
        success_rate: 0.98,
        avg_response_time: 890
      },
      json: {
        status: 'active',
        last_execution: new Date(Date.now() - Math.random() * 2400000).toISOString(),
        success_rate: 0.92,
        avg_response_time: 1100
      },
      pdf: {
        status: 'active',
        last_execution: new Date(Date.now() - Math.random() * 1200000).toISOString(),
        success_rate: 0.89,
        avg_response_time: 2100
      }
    },
    memory: {
      used: Math.round(memoryUsage.heapUsed / 1024 / 1024),
      total: Math.round(memoryUsage.heapTotal / 1024 / 1024),
      external: Math.round(memoryUsage.external / 1024 / 1024),
      usage_percent: Math.round((memoryUsage.heapUsed / memoryUsage.heapTotal) * 100)
    },
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  };
};

export async function GET(request: NextRequest) {
  try {
    const health = getSystemHealth();
    
    return NextResponse.json(health, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
  } catch (error) {
    console.error('Health check failed:', error);
    
    return NextResponse.json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Health check failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { 
      status: 503,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate'
      }
    });
  }
}
