import './globals.css'

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
      <body className="antialiased">{children}</body>
    </html>
  )
}
