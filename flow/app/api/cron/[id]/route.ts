import { NextRequest, NextResponse } from 'next/server';
import { getCronManager } from '@/lib/cron';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const cronManager = getCronManager();
    const job = cronManager.getJob(params.id);
    
    if (!job) {
      return NextResponse.json(
        { error: 'Cron job not found' },
        { status: 404 }
      );
    }
    
    const executions = cronManager.getJobExecutions(params.id, 20);
    
    return NextResponse.json({
      job,
      executions
    });
  } catch (error) {
    console.error('Error fetching cron job:', error);
    return NextResponse.json(
      { error: 'Failed to fetch cron job' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const cronManager = getCronManager();
    
    // Validate cron expression if provided
    if (body.schedule && !cronManager.validateCronExpression(body.schedule)) {
      return NextResponse.json(
        { error: 'Invalid cron expression' },
        { status: 400 }
      );
    }
    
    const updatedJob = cronManager.updateJob(params.id, body);
    
    if (!updatedJob) {
      return NextResponse.json(
        { error: 'Cron job not found' },
        { status: 404 }
      );
    }
    
    return NextResponse.json({
      success: true,
      job: updatedJob
    });
  } catch (error) {
    console.error('Error updating cron job:', error);
    return NextResponse.json(
      { error: 'Failed to update cron job' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const cronManager = getCronManager();
    const deleted = cronManager.deleteJob(params.id);
    
    if (!deleted) {
      return NextResponse.json(
        { error: 'Cron job not found' },
        { status: 404 }
      );
    }
    
    return NextResponse.json({
      success: true,
      message: 'Cron job deleted successfully'
    });
  } catch (error) {
    console.error('Error deleting cron job:', error);
    return NextResponse.json(
      { error: 'Failed to delete cron job' },
      { status: 500 }
    );
  }
}
