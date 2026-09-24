import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { DownloadSection } from '@/components/landing/download-section'
import { HowItWorksSection } from '@/components/landing/how-it-works-section'
import { CookieNotice } from '@/components/cookie-notice'
import { PLATFORMS, RELEASES_URL, DISCUSSIONS_URL } from '@/lib/links'
import { SITE_NAV_PATHS } from '@/lib/site'
import ContributionPage from '@/app/contribution/page'
import CookiesPage from '@/app/legal/cookies/page'
import PrivacyPage from '@/app/legal/privacy/page'

describe('Landing smoke', () => {
    it('exposes GitHub release downloads for every platform', () => {
        expect(PLATFORMS.map((p) => p.id)).toEqual(['windows', 'macos', 'linux'])
        expect(RELEASES_URL).toContain('/releases/latest')
        expect(DISCUSSIONS_URL).toContain('/discussions')
    })

    it('renders the download section with desktop platforms', () => {
        render(<DownloadSection />)
        expect(screen.getByText('Download VoxLabs')).toBeTruthy()
        expect(screen.getByText('Windows')).toBeTruthy()
        expect(screen.getByText('macOS')).toBeTruthy()
        expect(screen.getByText('Linux')).toBeTruthy()
        expect(screen.getByText(/desktop application/i)).toBeTruthy()
    })

    it('explains local desktop workflow', () => {
        render(<HowItWorksSection />)
        expect(screen.getByText('How VoxLabs Works')).toBeTruthy()
        expect(screen.getByText('Download')).toBeTruthy()
        expect(screen.getByText('Stay local')).toBeTruthy()
    })

    it('keeps GitHub Discussions on the Contribution page', () => {
        render(<ContributionPage />)
        expect(screen.getByRole('heading', { name: 'Contribution' })).toBeTruthy()
        expect(screen.getByText('Discussions')).toBeTruthy()
        expect(screen.getByText('Open GitHub Discussions')).toBeTruthy()
        expect(screen.queryByText('Open Source')).toBeNull()
        expect(DISCUSSIONS_URL).toContain('/discussions')
    })

    it('covers privacy, cookies, and indexable routes', () => {
        expect(SITE_NAV_PATHS).toContain('/legal/privacy/')
        expect(SITE_NAV_PATHS).toContain('/legal/cookies/')
        expect(SITE_NAV_PATHS).toContain('/legal/terms/')
        render(<PrivacyPage />)
        expect(screen.getByRole('heading', { name: 'Privacy Policy' })).toBeTruthy()
        expect(screen.getByText(/does not use advertising or analytics cookies/i)).toBeTruthy()
        render(<CookiesPage />)
        expect(screen.getByRole('heading', { name: 'Cookie Policy' })).toBeTruthy()
        expect(screen.getByRole('heading', { name: /we do not use tracking cookies/i })).toBeTruthy()
    })

    it('shows a cookie notice that can be dismissed', async () => {
        window.localStorage.clear()
        render(<CookieNotice />)
        await waitFor(() => {
            expect(screen.getByLabelText('Cookie and privacy notice')).toBeTruthy()
        })
        expect(screen.getByText(/does not use tracking or advertising cookies/i)).toBeTruthy()
    })
})
