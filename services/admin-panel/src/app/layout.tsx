import './globals.css'
import Navigation from '../components/Navigation'

export const metadata = {
  title: 'AI 가드레일 관리자 - SDC Admin Panel',
  description: 'AI Guardrail Management Dashboard for SDC',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="antialiased">
        <Navigation />
        {children}
      </body>
    </html>
  )
}
