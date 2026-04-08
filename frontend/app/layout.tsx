import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SQL Optimization RL Environment',
  description:
    'Meta x PyTorch OpenEnv Hackathon 2026 — Train AI agents to optimize SQL queries',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body
        className={inter.className}
        style={{
          background: '#0A0B1A',
          margin: 0,
        }}
      >
        {children}
      </body>
    </html>
  )
}