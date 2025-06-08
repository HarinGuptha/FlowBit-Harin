import { NextRequest, NextResponse } from 'next/server';

// Mock stats data - in production this would come from database/analytics
const getSystemStats = () => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const thisWeek = new Date(today.getTime() - (7 * 24 * 60 * 60 * 1000));
  const thisMonth = new Date(today.getFullYear(), today.getMonth(), 1);

  return {
    timestamp: now.toISOString(),
    period: {
      current_time: now.toISOString(),
      today: today.toISOString(),
      week_start: thisWeek.toISOString(),
      month_start: thisMonth.toISOString()
    },
    execution_counts: {
      total: {
        all_time: 15847,
        today: 234,
        this_week: 1456,
        this_month: 6789
      },
      by_engine: {
        langflow: {
          all_time: 8923,
          today: 156,
          this_week: 892,
          this_month: 3456
        },
        n8n: {
          all_time: 6924,
          today: 78,
          this_week: 564,
          this_month: 3333
        }
      },
      by_agent: {
        classifier: {
          all_time: 4234,
          today: 67,
          this_week: 423,
          this_month: 1678,
          success_rate: 0.95
        },
        email: {
          all_time: 3456,
          today: 45,
          this_week: 334,
          this_month: 1234,
          success_rate: 0.98
        },
        json: {
          all_time: 2890,
          today: 34,
          this_week: 267,
          this_month: 1089,
          success_rate: 0.92
        },
        pdf: {
          all_time: 2343,
          today: 10,
          this_week: 168,
          this_month: 789,
          success_rate: 0.89
        }
      }
    },
    format_processing: {
      email: {
        total_processed: 5678,
        complaints_detected: 1234,
        escalations_triggered: 456,
        avg_sentiment_score: -0.23,
        top_issues: ['billing', 'delivery', 'product_quality', 'support_response']
      },
      json: {
        total_processed: 4567,
        anomalies_detected: 234,
        high_risk_transactions: 67,
        avg_anomaly_score: 0.15,
        validation_failures: 89
      },
      pdf: {
        total_processed: 3456,
        compliance_flags: 123,
        high_value_documents: 45,
        gdpr_documents: 78,
        extraction_accuracy: 0.94
      }
    },
    anomaly_detection: {
      total_anomalies: 567,
      high_severity: 89,
      medium_severity: 234,
      low_severity: 244,
      false_positives: 23,
      accuracy_rate: 0.91,
      recent_patterns: [
        {
          type: 'unusual_transaction_amount',
          count: 45,
          severity: 'high',
          last_detected: new Date(Date.now() - Math.random() * 3600000).toISOString()
        },
        {
          type: 'suspicious_email_pattern',
          count: 23,
          severity: 'medium',
          last_detected: new Date(Date.now() - Math.random() * 1800000).toISOString()
        },
        {
          type: 'compliance_violation',
          count: 12,
          severity: 'high',
          last_detected: new Date(Date.now() - Math.random() * 7200000).toISOString()
        }
      ]
    },
    compliance_tracking: {
      gdpr_documents: 234,
      hipaa_documents: 67,
      sox_documents: 45,
      pci_documents: 23,
      compliance_score: 0.87,
      violations_detected: 12,
      remediation_required: 5
    },
    performance_metrics: {
      avg_response_time: {
        classifier: 1250,
        email: 890,
        json: 1100,
        pdf: 2100
      },
      throughput: {
        requests_per_minute: 45,
        peak_rpm: 156,
        avg_rpm_today: 67
      },
      error_rates: {
        classifier: 0.05,
        email: 0.02,
        json: 0.08,
        pdf: 0.11
      }
    },
    real_time_metrics: {
      active_executions: Math.floor(Math.random() * 10) + 1,
      queue_length: Math.floor(Math.random() * 25),
      cpu_usage: Math.floor(Math.random() * 30) + 20,
      memory_usage: Math.floor(Math.random() * 40) + 30,
      last_updated: now.toISOString()
    },
    trending: {
      most_active_agent: 'classifier',
      busiest_hour: '14:00',
      peak_day: 'Tuesday',
      growth_rate: {
        daily: 0.12,
        weekly: 0.08,
        monthly: 0.15
      }
    }
  };
};

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || 'all';
    const agent = searchParams.get('agent');
    const format = searchParams.get('format');

    let stats = getSystemStats();

    // Filter by agent if specified
    if (agent && stats.execution_counts.by_agent[agent]) {
      stats = {
        ...stats,
        filtered_by: `agent:${agent}`,
        agent_specific: stats.execution_counts.by_agent[agent]
      };
    }

    // Filter by format if specified
    if (format && stats.format_processing[format]) {
      stats = {
        ...stats,
        filtered_by: `format:${format}`,
        format_specific: stats.format_processing[format]
      };
    }

    return NextResponse.json(stats, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
  } catch (error) {
    console.error('Stats fetch failed:', error);
    
    return NextResponse.json({
      error: 'Failed to fetch stats',
      timestamp: new Date().toISOString(),
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { 
      status: 500,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate'
      }
    });
  }
}
