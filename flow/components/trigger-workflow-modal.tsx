"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Copy, Play, Webhook, Clock, CheckCircle, AlertCircle } from "lucide-react"
import { toast } from "sonner"

interface TriggerWorkflowModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  workflowId: string | null
  workflowName: string | null
  engine: string | null
}

export function TriggerWorkflowModal({ 
  open, 
  onOpenChange, 
  workflowId, 
  workflowName, 
  engine 
}: TriggerWorkflowModalProps) {
  const [activeTab, setActiveTab] = useState("manual")
  const [manualInput, setManualInput] = useState("")
  const [cronExpression, setCronExpression] = useState("0 9 * * 1-5")
  const [cronDescription, setCronDescription] = useState("Run every weekday at 9 AM")
  const [cronEnabled, setCronEnabled] = useState(true)
  const [isTriggering, setIsTriggering] = useState(false)
  const [webhookUrl, setWebhookUrl] = useState("")

  // Generate webhook URL when modal opens
  useState(() => {
    if (workflowId) {
      const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'
      setWebhookUrl(`${baseUrl}/api/hooks/${workflowId}`)
    }
  }, [workflowId])

  const handleManualTrigger = async () => {
    if (!workflowId || !engine) return

    setIsTriggering(true)
    try {
      let inputPayload = {}
      
      if (manualInput.trim()) {
        try {
          inputPayload = JSON.parse(manualInput)
        } catch {
          inputPayload = { content: manualInput }
        }
      }

      const response = await fetch('/api/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflowId,
          engine,
          triggerType: 'manual',
          inputPayload
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to trigger workflow: ${response.statusText}`)
      }

      const result = await response.json()
      toast.success(`Workflow triggered successfully! Run ID: ${result.result?.run_id || 'N/A'}`)
      onOpenChange(false)
    } catch (error) {
      console.error('Error triggering workflow:', error)
      toast.error('Failed to trigger workflow')
    } finally {
      setIsTriggering(false)
    }
  }

  const handleScheduleCreate = async () => {
    if (!workflowId || !engine) return

    setIsTriggering(true)
    try {
      let inputPayload = {}
      
      if (manualInput.trim()) {
        try {
          inputPayload = JSON.parse(manualInput)
        } catch {
          inputPayload = { content: manualInput }
        }
      }

      const response = await fetch('/api/cron', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflowId,
          engine,
          schedule: cronExpression,
          inputPayload,
          description: cronDescription,
          enabled: cronEnabled
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to create schedule: ${response.statusText}`)
      }

      const result = await response.json()
      toast.success(`Schedule created successfully! Job ID: ${result.job?.id}`)
      onOpenChange(false)
    } catch (error) {
      console.error('Error creating schedule:', error)
      toast.error('Failed to create schedule')
    } finally {
      setIsTriggering(false)
    }
  }

  const copyWebhookUrl = () => {
    navigator.clipboard.writeText(webhookUrl)
    toast.success('Webhook URL copied to clipboard!')
  }

  const validateCronExpression = (expression: string) => {
    // Basic cron validation - in production, use a proper cron parser
    const parts = expression.trim().split(/\s+/)
    return parts.length === 5
  }

  const getCronDescription = (expression: string) => {
    // Simplified cron description - in production, use a proper cron parser
    if (expression === "0 9 * * 1-5") return "Every weekday at 9:00 AM"
    if (expression === "0 0 * * *") return "Every day at midnight"
    if (expression === "0 */6 * * *") return "Every 6 hours"
    if (expression === "*/15 * * * *") return "Every 15 minutes"
    return "Custom schedule"
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Play className="w-5 h-5" />
            Trigger Workflow
          </DialogTitle>
          {workflowName && (
            <DialogDescription className="flex items-center gap-2 mt-2">
              {workflowName} • <Badge variant="outline">{engine}</Badge>
            </DialogDescription>
          )}
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="manual">Manual</TabsTrigger>
            <TabsTrigger value="webhook">Webhook</TabsTrigger>
            <TabsTrigger value="schedule">Schedule</TabsTrigger>
          </TabsList>

          <TabsContent value="manual" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Manual Trigger</CardTitle>
                <CardDescription>
                  Trigger the workflow immediately with optional input data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="manual-input">Input Payload (JSON or Text)</Label>
                  <Textarea
                    id="manual-input"
                    placeholder='{"content": "Your input data here..."}'
                    value={manualInput}
                    onChange={(e) => setManualInput(e.target.value)}
                    rows={6}
                    className="mt-2"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Enter JSON data or plain text. Leave empty for default trigger.
                  </p>
                </div>
                <Button 
                  onClick={handleManualTrigger} 
                  disabled={isTriggering}
                  className="w-full"
                >
                  {isTriggering ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Triggering...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Trigger Now
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="webhook" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Webhook className="w-5 h-5" />
                  Webhook Endpoint
                </CardTitle>
                <CardDescription>
                  Public URL that can be called to trigger this workflow
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Webhook URL</Label>
                  <div className="flex gap-2 mt-2">
                    <Input
                      value={webhookUrl}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={copyWebhookUrl}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Usage Example:</h4>
                  <pre className="text-sm bg-gray-800 text-gray-100 p-3 rounded overflow-x-auto">
{`curl -X POST ${webhookUrl} \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Your data here"}'`}
                  </pre>
                </div>

                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Webhook is active and ready to receive requests</span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="schedule" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Schedule Workflow
                </CardTitle>
                <CardDescription>
                  Set up automatic execution on a schedule using cron expressions
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="cron-expression">Cron Expression</Label>
                  <Input
                    id="cron-expression"
                    value={cronExpression}
                    onChange={(e) => {
                      setCronExpression(e.target.value)
                      setCronDescription(getCronDescription(e.target.value))
                    }}
                    placeholder="0 9 * * 1-5"
                    className="mt-2 font-mono"
                  />
                  <div className="flex items-center gap-2 mt-1">
                    {validateCronExpression(cronExpression) ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-600" />
                    )}
                    <span className="text-sm text-gray-600">{cronDescription}</span>
                  </div>
                </div>

                <div>
                  <Label htmlFor="cron-description">Description</Label>
                  <Input
                    id="cron-description"
                    value={cronDescription}
                    onChange={(e) => setCronDescription(e.target.value)}
                    placeholder="Describe when this should run"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="schedule-input">Input Payload (JSON or Text)</Label>
                  <Textarea
                    id="schedule-input"
                    placeholder='{"content": "Scheduled execution data..."}'
                    value={manualInput}
                    onChange={(e) => setManualInput(e.target.value)}
                    rows={4}
                    className="mt-2"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="cron-enabled"
                    checked={cronEnabled}
                    onCheckedChange={setCronEnabled}
                  />
                  <Label htmlFor="cron-enabled">Enable schedule immediately</Label>
                </div>

                <Button 
                  onClick={handleScheduleCreate} 
                  disabled={isTriggering || !validateCronExpression(cronExpression)}
                  className="w-full"
                >
                  {isTriggering ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating Schedule...
                    </>
                  ) : (
                    <>
                      <Clock className="w-4 h-4 mr-2" />
                      Create Schedule
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
