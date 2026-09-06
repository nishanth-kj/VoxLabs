'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from "recharts"

interface ChartCardProps {
    title: string
    description?: string
    data: any[]
    type?: 'line' | 'area' | 'bar'
    dataKeys: {
        key: string
        label: string
        color: string
    }[]
    xAxisKey: string
}

export function ChartCard({
    title,
    description,
    data,
    type = 'line',
    dataKeys,
    xAxisKey
}: ChartCardProps) {
    const renderChart = () => {
        const commonProps = {
            data,
            margin: { top: 10, right: 10, left: 0, bottom: 0 }
        }

        switch (type) {
            case 'area':
                return (
                    <AreaChart {...commonProps}>
                        <defs>
                            {dataKeys.map((dk, idx) => (
                                <linearGradient key={idx} id={`gradient-${idx}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={dk.color} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={dk.color} stopOpacity={0} />
                                </linearGradient>
                            ))}
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                            dataKey={xAxisKey}
                            className="text-xs"
                            stroke="hsl(var(--muted-foreground))"
                        />
                        <YAxis
                            className="text-xs"
                            stroke="hsl(var(--muted-foreground))"
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--card))',
                                border: '1px solid hsl(var(--border))',
                                borderRadius: '8px'
                            }}
                        />
                        <Legend />
                        {dataKeys.map((dk, idx) => (
                            <Area
                                key={idx}
                                type="monotone"
                                dataKey={dk.key}
                                name={dk.label}
                                stroke={dk.color}
                                fill={`url(#gradient-${idx})`}
                                strokeWidth={2}
                            />
                        ))}
                    </AreaChart>
                )

            case 'bar':
                return (
                    <BarChart {...commonProps}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                            dataKey={xAxisKey}
                            className="text-xs"
                            stroke="hsl(var(--muted-foreground))"
                        />
                        <YAxis
                            className="text-xs"
                            stroke="hsl(var(--muted-foreground))"
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--card))',
                                border: '1px solid hsl(var(--border))',
                                borderRadius: '8px'
                            }}
                        />
                        <Legend />
                        {dataKeys.map((dk, idx) => (
                            <Bar
                                key={idx}
                                dataKey={dk.key}
                                name={dk.label}
                                fill={dk.color}
                                radius={[4, 4, 0, 0]}
                            />
                        ))}
                    </BarChart>
                )

            default: // line
                return (
                    <LineChart {...commonProps}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                            dataKey={xAxisKey}
                            className="text-xs"
                            stroke="hsl(var(--muted-foreground))"
                        />
                        <YAxis
                            className="text-xs"
                            stroke="hsl(var(--muted-foreground))"
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--card))',
                                border: '1px solid hsl(var(--border))',
                                borderRadius: '8px'
                            }}
                        />
                        <Legend />
                        {dataKeys.map((dk, idx) => (
                            <Line
                                key={idx}
                                type="monotone"
                                dataKey={dk.key}
                                name={dk.label}
                                stroke={dk.color}
                                strokeWidth={2}
                                dot={{ fill: dk.color, r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                        ))}
                    </LineChart>
                )
        }
    }

    return (
        <Card className="bg-card/50 border-border/40">
            <CardHeader>
                <CardTitle className="text-xl">{title}</CardTitle>
                {description && (
                    <p className="text-sm text-muted-foreground">{description}</p>
                )}
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    {renderChart()}
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}
