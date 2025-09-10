import type { Metadata } from 'next'
import { Inter, JetBrains_Mono, Noto_Sans_KR } from 'next/font/google'
import './globals.css'
import { cn } from '@/lib/utils'
import { ThemeProvider } from '@/components/theme-provider'
import { ClientToaster } from '@/components/client-toaster'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter'
})

const notoSansKR = Noto_Sans_KR({
  subsets: ['latin'],
  variable: '--font-noto-sans-kr'
})

const jetbrainsMono = JetBrains_Mono({ 
  subsets: ['latin'],
  variable: '--font-jetbrains-mono'
})

export const metadata: Metadata = {
  title: 'SDC Gen AI',
  description: '멀티 LLM 기반 대화형 AI 서비스',
  keywords: ['AI', 'Chat', 'Document', 'RAG', 'LLM', '한국어'],
  authors: [{ name: 'SDC Gen AI Team' }],
  creator: 'SDC Gen AI Team',
  publisher: 'SDC Gen AI',
  robots: {
    index: false,
    follow: false,
  },
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0a0a' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className={cn(
        'min-h-screen bg-background font-sans antialiased',
        inter.variable,
        notoSansKR.variable,
        jetbrainsMono.variable
      )}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <div className="relative flex min-h-screen flex-col">
            <div className="flex-1">{children}</div>
          </div>
          <ClientToaster />
        </ThemeProvider>
      </body>
    </html>
  )
}