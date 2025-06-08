import { NextRequest, NextResponse } from 'next/server';
import { getCronManager } from '@/lib/cron';

export async function GET(request: NextRequest) {
  try {
    const cronManager = getCronManager();
    const jobs = cronManager.getAllJobs();
    
    return NextResponse.json({
      jobs,
      total: jobs.length
    });
  } catch (error) {
    console.error('Error fetching cron jobs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch cron jobs' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { workflowId, engine, schedule, inputPayload, description, enabled = true } = body;
    
    if (!workflowId || !engine || !schedule) {
      return NextResponse.json(
        { error: 'Missing required fields: workflowId, engine, schedule' },
        { status: 400 }
      );
    }
    
    const cronManager = getCronManager();
    
    // Validate cron expression
    if (!cronManager.validateCronExpression(schedule)) {
      return NextResponse.json(
        { error: 'Invalid cron expression' },
        { status: 400 }
      );
    }
    
    const job = cronManager.createJob({
      workflowId,
      engine,
      schedule,
      inputPayload,
      description,
      enabled
    });
    
    return NextResponse.json({
      success: true,
      job
    });
  } catch (error) {
    console.error('Error creating cron job:', error);
    return NextResponse.json(
      { error: 'Failed to create cron job' },
      { status: 500 }
    );
  }
}
