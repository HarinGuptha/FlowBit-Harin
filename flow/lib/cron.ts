import * as cron from 'node-cron';
import fs from 'fs';
import path from 'path';

interface CronJob {
  id: string;
  workflowId: string;
  engine: string;
  schedule: string;
  inputPayload?: any;
  enabled: boolean;
  createdAt: string;
  lastRun?: string;
  nextRun?: string;
  description?: string;
}

interface CronJobExecution {
  id: string;
  jobId: string;
  timestamp: string;
  status: 'success' | 'failed';
  runId?: string;
  error?: string;
}

class CronManager {
  private jobs: Map<string, CronJob> = new Map();
  private tasks: Map<string, cron.ScheduledTask> = new Map();
  private executions: CronJobExecution[] = [];
  private jobsFilePath: string;
  private executionsFilePath: string;

  constructor() {
    this.jobsFilePath = path.join(process.cwd(), 'data', 'cron-jobs.json');
    this.executionsFilePath = path.join(process.cwd(), 'data', 'cron-executions.json');
    this.ensureDataDirectory();
    this.loadJobs();
    this.loadExecutions();
  }

  private ensureDataDirectory() {
    const dataDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
  }

  private loadJobs() {
    try {
      if (fs.existsSync(this.jobsFilePath)) {
        const data = fs.readFileSync(this.jobsFilePath, 'utf8');
        const jobs: CronJob[] = JSON.parse(data);
        
        jobs.forEach(job => {
          this.jobs.set(job.id, job);
          if (job.enabled) {
            this.scheduleJob(job);
          }
        });
        
        console.log(`Loaded ${jobs.length} cron jobs`);
      }
    } catch (error) {
      console.error('Error loading cron jobs:', error);
    }
  }

  private loadExecutions() {
    try {
      if (fs.existsSync(this.executionsFilePath)) {
        const data = fs.readFileSync(this.executionsFilePath, 'utf8');
        this.executions = JSON.parse(data);
        
        // Keep only last 1000 executions
        if (this.executions.length > 1000) {
          this.executions = this.executions.slice(-1000);
          this.saveExecutions();
        }
      }
    } catch (error) {
      console.error('Error loading cron executions:', error);
    }
  }

  private saveJobs() {
    try {
      const jobs = Array.from(this.jobs.values());
      fs.writeFileSync(this.jobsFilePath, JSON.stringify(jobs, null, 2));
    } catch (error) {
      console.error('Error saving cron jobs:', error);
    }
  }

  private saveExecutions() {
    try {
      fs.writeFileSync(this.executionsFilePath, JSON.stringify(this.executions, null, 2));
    } catch (error) {
      console.error('Error saving cron executions:', error);
    }
  }

  private scheduleJob(job: CronJob) {
    try {
      const task = cron.schedule(job.schedule, async () => {
        await this.executeJob(job);
      }, {
        scheduled: false
      });

      this.tasks.set(job.id, task);
      task.start();
      
      // Update next run time
      job.nextRun = this.getNextRunTime(job.schedule);
      this.saveJobs();
      
      console.log(`Scheduled cron job: ${job.id} with schedule: ${job.schedule}`);
    } catch (error) {
      console.error(`Error scheduling job ${job.id}:`, error);
    }
  }

  private async executeJob(job: CronJob) {
    const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const execution: CronJobExecution = {
      id: executionId,
      jobId: job.id,
      timestamp: new Date().toISOString(),
      status: 'success'
    };

    try {
      console.log(`Executing cron job: ${job.id}`);
      
      // Trigger the workflow
      const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/api/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflowId: job.workflowId,
          engine: job.engine,
          triggerType: 'cron',
          inputPayload: job.inputPayload
        })
      });

      if (!response.ok) {
        throw new Error(`Trigger API error: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      execution.runId = result.result?.run_id || result.result?.executionId;
      
      // Update job last run time
      job.lastRun = execution.timestamp;
      job.nextRun = this.getNextRunTime(job.schedule);
      this.saveJobs();
      
      console.log(`Cron job ${job.id} executed successfully. Run ID: ${execution.runId}`);
      
    } catch (error) {
      execution.status = 'failed';
      execution.error = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Cron job ${job.id} failed:`, error);
    }

    // Save execution record
    this.executions.push(execution);
    if (this.executions.length > 1000) {
      this.executions = this.executions.slice(-1000);
    }
    this.saveExecutions();
  }

  private getNextRunTime(schedule: string): string {
    try {
      // This is a simplified implementation
      // In production, use a proper cron parser library
      const now = new Date();
      const nextRun = new Date(now.getTime() + 60000); // Add 1 minute as placeholder
      return nextRun.toISOString();
    } catch (error) {
      return new Date(Date.now() + 3600000).toISOString(); // 1 hour from now
    }
  }

  public createJob(jobData: Omit<CronJob, 'id' | 'createdAt' | 'nextRun'>): CronJob {
    const job: CronJob = {
      ...jobData,
      id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date().toISOString(),
      nextRun: this.getNextRunTime(jobData.schedule)
    };

    this.jobs.set(job.id, job);
    
    if (job.enabled) {
      this.scheduleJob(job);
    }
    
    this.saveJobs();
    return job;
  }

  public updateJob(jobId: string, updates: Partial<CronJob>): CronJob | null {
    const job = this.jobs.get(jobId);
    if (!job) return null;

    // Stop existing task if schedule changed or job disabled
    if (updates.schedule !== undefined || updates.enabled === false) {
      this.stopJob(jobId);
    }

    // Update job
    Object.assign(job, updates);
    
    // Reschedule if enabled and schedule might have changed
    if (job.enabled && (updates.schedule !== undefined || updates.enabled === true)) {
      job.nextRun = this.getNextRunTime(job.schedule);
      this.scheduleJob(job);
    }

    this.saveJobs();
    return job;
  }

  public deleteJob(jobId: string): boolean {
    const job = this.jobs.get(jobId);
    if (!job) return false;

    this.stopJob(jobId);
    this.jobs.delete(jobId);
    this.saveJobs();
    return true;
  }

  public stopJob(jobId: string): boolean {
    const task = this.tasks.get(jobId);
    if (task) {
      task.stop();
      this.tasks.delete(jobId);
      return true;
    }
    return false;
  }

  public getJob(jobId: string): CronJob | null {
    return this.jobs.get(jobId) || null;
  }

  public getAllJobs(): CronJob[] {
    return Array.from(this.jobs.values());
  }

  public getJobExecutions(jobId: string, limit: number = 50): CronJobExecution[] {
    return this.executions
      .filter(exec => exec.jobId === jobId)
      .slice(-limit)
      .reverse();
  }

  public getAllExecutions(limit: number = 100): CronJobExecution[] {
    return this.executions.slice(-limit).reverse();
  }

  public validateCronExpression(expression: string): boolean {
    return cron.validate(expression);
  }
}

// Singleton instance
let cronManager: CronManager | null = null;

export function getCronManager(): CronManager {
  if (!cronManager) {
    cronManager = new CronManager();
  }
  return cronManager;
}

export type { CronJob, CronJobExecution };
