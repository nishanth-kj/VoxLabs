'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ActivityLog } from "@/lib/mock-data"
import { formatRelativeTime } from "@/lib/dashboard-utils"
import {
    UserPlus,
    Mic,
    Activity,
    CreditCard,
    User,
    Settings,
    LucideIcon
} from "lucide-react"
import { cn } from "@/lib/utils"

interface ActivityFeedProps {
    activities: ActivityLog[]
    maxItems?: number
}

const activityIcons: Record<string, LucideIcon> = {
    user_created: UserPlus,
    voice_cloned: Mic,
    api_call: Activity,
    subscription_changed: CreditCard,
    user_updated: User,
    system_event: Settings,
}

const activityColors: Record<string, string> = {
    user_created: 'bg-green-100 text-green-600 dark:bg-green-950/30 dark:text-green-400',
    voice_cloned: 'bg-purple-100 text-purple-600 dark:bg-purple-950/30 dark:text-purple-400',
    api_call: 'bg-blue-100 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400',
    subscription_changed: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-950/30 dark:text-indigo-400',
    user_updated: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-950/30 dark:text-yellow-400',
    system_event: 'bg-gray-100 text-gray-600 dark:bg-gray-950/30 dark:text-gray-400',
}

export function ActivityFeed({ activities, maxItems = 10 }: ActivityFeedProps) {
    const displayActivities = activities.slice(0, maxItems)

    return (
        <Card className="bg-card/50 border-border/40">
            <CardHeader>
                <CardTitle className="text-xl">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {displayActivities.map((activity, index) => {
                        const Icon = activityIcons[activity.type] || Activity
                        const colorClass = activityColors[activity.type] || activityColors.system_event

                        return (
                            <div
                                key={activity.id}
                                className={cn(
                                    "flex items-start gap-4 pb-4",
                                    index !== displayActivities.length - 1 && "border-b border-border/40"
                                )}
                            >
                                <div className={cn(
                                    "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0",
                                    colorClass
                                )}>
                                    <Icon className="w-5 h-5" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-foreground">
                                        {activity.description}
                                    </p>
                                    {activity.user && (
                                        <p className="text-xs text-muted-foreground mt-0.5">
                                            by {activity.user}
                                        </p>
                                    )}
                                    <p className="text-xs text-muted-foreground mt-1">
                                        {formatRelativeTime(activity.timestamp)}
                                    </p>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </CardContent>
        </Card>
    )
}
