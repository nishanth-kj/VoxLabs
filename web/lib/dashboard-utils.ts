// Utility functions for dashboard data processing

import { format, formatDistanceToNow } from 'date-fns'

/**
 * Format a number with commas for thousands
 */
export function formatNumber(num: number): string {
    return new Intl.NumberFormat('en-US').format(num)
}

/**
 * Format a number as currency
 */
export function formatCurrency(amount: number, currency = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency,
    }).format(amount)
}

/**
 * Calculate percentage change between two numbers
 */
export function calculatePercentageChange(current: number, previous: number): number {
    if (previous === 0) return 100
    return ((current - previous) / previous) * 100
}

/**
 * Format percentage with sign
 */
export function formatPercentage(value: number, decimals = 1): string {
    const sign = value > 0 ? '+' : ''
    return `${sign}${value.toFixed(decimals)}%`
}

/**
 * Format date to readable string
 */
export function formatDate(date: string | Date, formatStr = 'MMM d, yyyy'): string {
    return format(new Date(date), formatStr)
}

/**
 * Format date as relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
    return formatDistanceToNow(new Date(date), { addSuffix: true })
}

/**
 * Get trend indicator based on percentage change
 */
export function getTrendIndicator(change: number): 'up' | 'down' | 'neutral' {
    if (change > 0) return 'up'
    if (change < 0) return 'down'
    return 'neutral'
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let size = bytes
    let unitIndex = 0

    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex++
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`
}

/**
 * Get status color based on status type
 */
export function getStatusColor(status: string): string {
    const colors: Record<string, string> = {
        active: 'text-green-600 dark:text-green-400',
        inactive: 'text-gray-600 dark:text-gray-400',
        suspended: 'text-red-600 dark:text-red-400',
        trial: 'text-yellow-600 dark:text-yellow-400',
        pending: 'text-orange-600 dark:text-orange-400',
    }
    return colors[status.toLowerCase()] || 'text-gray-600 dark:text-gray-400'
}

/**
 * Get plan badge color
 */
export function getPlanColor(plan: string): string {
    const colors: Record<string, string> = {
        free: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
        starter: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
        professional: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
        enterprise: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
    }
    return colors[plan.toLowerCase()] || colors.free
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
}

/**
 * Generate initials from name
 */
export function getInitials(name: string): string {
    return name
        .split(' ')
        .map(part => part[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
}
