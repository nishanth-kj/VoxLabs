'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowDown, ArrowUp, Minus, LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatsCardProps {
    title: string
    value: string | number
    change?: number
    changeLabel?: string
    icon: LucideIcon
    iconColor?: string
    trend?: 'up' | 'down' | 'neutral'
}

export function StatsCard({
    title,
    value,
    change,
    changeLabel,
    icon: Icon,
    iconColor = "text-indigo-500",
    trend
}: StatsCardProps) {
    // Auto-detect trend from change if not provided
    const actualTrend = trend || (change && change > 0 ? 'up' : change && change < 0 ? 'down' : 'neutral')

    const trendConfig = {
        up: {
            icon: ArrowUp,
            color: 'text-green-600 dark:text-green-400',
            bgColor: 'bg-green-50 dark:bg-green-950/30'
        },
        down: {
            icon: ArrowDown,
            color: 'text-red-600 dark:text-red-400',
            bgColor: 'bg-red-50 dark:bg-red-950/30'
        },
        neutral: {
            icon: Minus,
            color: 'text-gray-600 dark:text-gray-400',
            bgColor: 'bg-gray-50 dark:bg-gray-950/30'
        }
    }

    const TrendIcon = trendConfig[actualTrend].icon

    return (
        <Card className="bg-card/50 border-border/40 hover:border-border/80 transition-all duration-300 hover:shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                    {title}
                </CardTitle>
                <div className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center",
                    "bg-gradient-to-br from-secondary/80 to-secondary/40"
                )}>
                    <Icon className={cn("w-5 h-5", iconColor)} />
                </div>
            </CardHeader>
            <CardContent>
                <div className="text-3xl font-bold tracking-tight mb-1">
                    {value}
                </div>
                {(change !== undefined || changeLabel) && (
                    <div className="flex items-center gap-2 text-sm">
                        {change !== undefined && (
                            <div className={cn(
                                "flex items-center gap-1 px-2 py-0.5 rounded-full",
                                trendConfig[actualTrend].bgColor
                            )}>
                                <TrendIcon className={cn("w-3 h-3", trendConfig[actualTrend].color)} />
                                <span className={cn("font-medium", trendConfig[actualTrend].color)}>
                                    {Math.abs(change)}%
                                </span>
                            </div>
                        )}
                        {changeLabel && (
                            <span className="text-muted-foreground">
                                {changeLabel}
                            </span>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
