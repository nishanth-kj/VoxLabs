// Mock data for dashboard demonstrations

export interface User {
    id: string
    name: string
    email: string
    role: 'admin' | 'company_admin' | 'user'
    company?: string
    status: 'active' | 'inactive'
    joinedAt: string
    lastActive: string
    avatar?: string
}

export interface Company {
    id: string
    name: string
    plan: 'free' | 'starter' | 'professional' | 'enterprise'
    users: number
    voiceClones: number
    apiCalls: number
    createdAt: string
    status: 'active' | 'suspended' | 'trial'
}

export interface ActivityLog {
    id: string
    type: 'user_created' | 'voice_cloned' | 'api_call' | 'subscription_changed' | 'user_updated' | 'system_event'
    description: string
    user?: string
    timestamp: string
    icon?: string
}

export interface UsageStats {
    date: string
    apiCalls: number
    voiceClones: number
    users: number
}

// Mock Users
export const mockUsers: User[] = [
    {
        id: '1',
        name: 'John Doe',
        email: 'john@example.com',
        role: 'admin',
        status: 'active',
        joinedAt: '2024-01-15',
        lastActive: '2026-01-06T00:00:00',
    },
    {
        id: '2',
        name: 'Sarah Smith',
        email: 'sarah@techcorp.com',
        role: 'company_admin',
        company: 'TechCorp Inc.',
        status: 'active',
        joinedAt: '2024-03-20',
        lastActive: '2026-01-05T23:30:00',
    },
    {
        id: '3',
        name: 'Mike Johnson',
        email: 'mike@startup.io',
        role: 'company_admin',
        company: 'Startup.io',
        status: 'active',
        joinedAt: '2024-06-10',
        lastActive: '2026-01-05T22:15:00',
    },
    {
        id: '4',
        name: 'Emily Chen',
        email: 'emily@techcorp.com',
        role: 'user',
        company: 'TechCorp Inc.',
        status: 'active',
        joinedAt: '2024-07-01',
        lastActive: '2026-01-05T21:00:00',
    },
    {
        id: '5',
        name: 'David Wilson',
        email: 'david@example.com',
        role: 'user',
        status: 'inactive',
        joinedAt: '2024-02-28',
        lastActive: '2025-12-20T10:00:00',
    },
]

// Mock Companies
export const mockCompanies: Company[] = [
    {
        id: '1',
        name: 'TechCorp Inc.',
        plan: 'enterprise',
        users: 45,
        voiceClones: 128,
        apiCalls: 15420,
        createdAt: '2024-03-20',
        status: 'active',
    },
    {
        id: '2',
        name: 'Startup.io',
        plan: 'professional',
        users: 12,
        voiceClones: 34,
        apiCalls: 5230,
        createdAt: '2024-06-10',
        status: 'active',
    },
    {
        id: '3',
        name: 'Creative Agency',
        plan: 'starter',
        users: 5,
        voiceClones: 8,
        apiCalls: 890,
        createdAt: '2024-08-15',
        status: 'trial',
    },
    {
        id: '4',
        name: 'Media House',
        plan: 'professional',
        users: 28,
        voiceClones: 67,
        apiCalls: 8940,
        createdAt: '2024-05-01',
        status: 'active',
    },
]

// Mock Activity Logs
export const mockActivityLogs: ActivityLog[] = [
    {
        id: '1',
        type: 'user_created',
        description: 'New user registered: Emily Chen',
        user: 'Emily Chen',
        timestamp: '2026-01-05T23:45:00',
    },
    {
        id: '2',
        type: 'voice_cloned',
        description: 'Voice clone created by TechCorp Inc.',
        user: 'Sarah Smith',
        timestamp: '2026-01-05T23:30:00',
    },
    {
        id: '3',
        type: 'subscription_changed',
        description: 'Startup.io upgraded to Professional plan',
        user: 'Mike Johnson',
        timestamp: '2026-01-05T22:15:00',
    },
    {
        id: '4',
        type: 'api_call',
        description: '1,000+ API calls from TechCorp Inc.',
        timestamp: '2026-01-05T21:00:00',
    },
    {
        id: '5',
        type: 'user_updated',
        description: 'Profile updated: David Wilson',
        user: 'David Wilson',
        timestamp: '2026-01-05T20:30:00',
    },
    {
        id: '6',
        type: 'system_event',
        description: 'System backup completed successfully',
        timestamp: '2026-01-05T20:00:00',
    },
]

// Mock Usage Stats (Last 7 days)
export const mockUsageStats: UsageStats[] = [
    { date: '2026-01-01', apiCalls: 3200, voiceClones: 45, users: 12 },
    { date: '2026-01-02', apiCalls: 4100, voiceClones: 52, users: 18 },
    { date: '2026-01-03', apiCalls: 3800, voiceClones: 38, users: 15 },
    { date: '2026-01-04', apiCalls: 5200, voiceClones: 61, users: 22 },
    { date: '2026-01-05', apiCalls: 4900, voiceClones: 58, users: 20 },
    { date: '2026-01-06', apiCalls: 2100, voiceClones: 28, users: 9 },
]

// Company-specific mock data
export const mockCompanyStats = {
    teamMembers: 45,
    voiceClones: 128,
    apiCallsThisMonth: 15420,
    storageUsed: 24.5, // GB
    storageLimit: 100, // GB
}

export const mockCompanyTeam: User[] = mockUsers.filter(u => u.company === 'TechCorp Inc.')

export const mockCompanyActivity: ActivityLog[] = [
    {
        id: '1',
        type: 'voice_cloned',
        description: 'New voice clone created: "Professional Narrator"',
        user: 'Sarah Smith',
        timestamp: '2026-01-05T23:30:00',
    },
    {
        id: '2',
        type: 'user_created',
        description: 'New team member added: Emily Chen',
        user: 'Sarah Smith',
        timestamp: '2026-01-05T22:00:00',
    },
    {
        id: '3',
        type: 'api_call',
        description: 'Generated 150 audio files',
        user: 'Emily Chen',
        timestamp: '2026-01-05T21:15:00',
    },
]
