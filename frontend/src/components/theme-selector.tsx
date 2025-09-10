"use client"

import * as React from "react"
import { Check, Palette } from "lucide-react"
import { useTheme } from "next-themes"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const themes = [
  {
    name: "default",
    label: "기본",
    color: "bg-gradient-to-br from-slate-900 to-slate-50"
  },
  {
    name: "ocean",
    label: "오션",
    color: "bg-gradient-to-br from-blue-600 to-blue-100"
  },
  {
    name: "forest",
    label: "포레스트",
    color: "bg-gradient-to-br from-green-600 to-green-100"
  },
  {
    name: "rose",
    label: "로즈",
    color: "bg-gradient-to-br from-rose-600 to-rose-100"
  }
]

interface ThemeSelectorProps {
  className?: string
}

export function ThemeSelector({ className }: ThemeSelectorProps) {
  const { theme } = useTheme() // Get current light/dark theme
  const [selectedTheme, setSelectedTheme] = React.useState("default")
  const [mounted, setMounted] = React.useState(false)
  
  const applyTheme = React.useCallback((themeName: string) => {
    const html = document.documentElement
    
    // Check both next-themes value and DOM classList for accurate detection
    const isDark = html.classList.contains('dark') || 
                   theme === 'dark' || 
                   (theme === 'system' && window.matchMedia?.('(prefers-color-scheme: dark)').matches)
    
    // Remove existing theme classes
    themes.forEach(themeItem => {
      html.classList.remove(`theme-${themeItem.name}`)
    })
    
    // Apply theme styles directly based on light/dark mode
    if (themeName === "ocean") {
      if (isDark) {
        // Ocean Dark Theme
        html.style.setProperty('--background', '210 100% 2%')
        html.style.setProperty('--foreground', '210 60% 92%')
        html.style.setProperty('--card', '210 100% 4%')
        html.style.setProperty('--card-foreground', '210 60% 92%')
        html.style.setProperty('--popover', '210 100% 4%')
        html.style.setProperty('--popover-foreground', '210 60% 92%')
        html.style.setProperty('--primary', '210 90% 60%')
        html.style.setProperty('--primary-foreground', '210 100% 2%')
        html.style.setProperty('--secondary', '210 40% 8%')
        html.style.setProperty('--secondary-foreground', '210 60% 92%')
        html.style.setProperty('--muted', '210 40% 6%')
        html.style.setProperty('--muted-foreground', '210 30% 50%')
        html.style.setProperty('--accent', '210 40% 10%')
        html.style.setProperty('--accent-foreground', '210 60% 92%')
        html.style.setProperty('--destructive', '0 84% 60%')
        html.style.setProperty('--destructive-foreground', '0 0% 100%')
        html.style.setProperty('--border', '210 40% 12%')
        html.style.setProperty('--input', '210 40% 6%')
        html.style.setProperty('--ring', '210 90% 60%')
      } else {
        // Ocean Light Theme
        html.style.setProperty('--background', '210 100% 97%')
        html.style.setProperty('--foreground', '210 40% 8%')
        html.style.setProperty('--card', '210 100% 100%')
        html.style.setProperty('--card-foreground', '210 40% 8%')
        html.style.setProperty('--popover', '210 100% 100%')
        html.style.setProperty('--popover-foreground', '210 40% 8%')
        html.style.setProperty('--primary', '210 90% 45%')
        html.style.setProperty('--primary-foreground', '210 100% 97%')
        html.style.setProperty('--secondary', '210 60% 90%')
        html.style.setProperty('--secondary-foreground', '210 40% 8%')
        html.style.setProperty('--muted', '210 60% 94%')
        html.style.setProperty('--muted-foreground', '210 30% 40%')
        html.style.setProperty('--accent', '210 80% 88%')
        html.style.setProperty('--accent-foreground', '210 40% 8%')
        html.style.setProperty('--destructive', '0 84% 60%')
        html.style.setProperty('--destructive-foreground', '0 0% 100%')
        html.style.setProperty('--border', '210 40% 85%')
        html.style.setProperty('--input', '210 60% 94%')
        html.style.setProperty('--ring', '210 90% 45%')
      }
      html.classList.add('theme-ocean')
    } else if (themeName === "forest") {
      if (isDark) {
        // Forest Dark Theme
        html.style.setProperty('--background', '120 30% 2%')
        html.style.setProperty('--foreground', '120 20% 92%')
        html.style.setProperty('--card', '120 30% 4%')
        html.style.setProperty('--card-foreground', '120 20% 92%')
        html.style.setProperty('--popover', '120 30% 4%')
        html.style.setProperty('--popover-foreground', '120 20% 92%')
        html.style.setProperty('--primary', '120 50% 55%')
        html.style.setProperty('--primary-foreground', '120 30% 2%')
        html.style.setProperty('--secondary', '120 20% 8%')
        html.style.setProperty('--secondary-foreground', '120 20% 92%')
        html.style.setProperty('--muted', '120 20% 6%')
        html.style.setProperty('--muted-foreground', '120 15% 50%')
        html.style.setProperty('--accent', '120 20% 10%')
        html.style.setProperty('--accent-foreground', '120 20% 92%')
        html.style.setProperty('--destructive', '0 84% 60%')
        html.style.setProperty('--destructive-foreground', '0 0% 100%')
        html.style.setProperty('--border', '120 20% 12%')
        html.style.setProperty('--input', '120 20% 6%')
        html.style.setProperty('--ring', '120 50% 55%')
      } else {
        // Forest Light Theme
        html.style.setProperty('--background', '120 30% 97%')
        html.style.setProperty('--foreground', '120 40% 8%')
        html.style.setProperty('--card', '120 30% 100%')
        html.style.setProperty('--card-foreground', '120 40% 8%')
        html.style.setProperty('--popover', '120 30% 100%')
        html.style.setProperty('--popover-foreground', '120 40% 8%')
        html.style.setProperty('--primary', '120 60% 35%')
        html.style.setProperty('--primary-foreground', '120 30% 97%')
        html.style.setProperty('--secondary', '120 30% 90%')
        html.style.setProperty('--secondary-foreground', '120 40% 8%')
        html.style.setProperty('--muted', '120 30% 94%')
        html.style.setProperty('--muted-foreground', '120 20% 40%')
        html.style.setProperty('--accent', '120 40% 88%')
        html.style.setProperty('--accent-foreground', '120 40% 8%')
        html.style.setProperty('--destructive', '0 84% 60%')
        html.style.setProperty('--destructive-foreground', '0 0% 100%')
        html.style.setProperty('--border', '120 30% 85%')
        html.style.setProperty('--input', '120 30% 94%')
        html.style.setProperty('--ring', '120 60% 35%')
      }
      html.classList.add('theme-forest')
    } else if (themeName === "rose") {
      if (isDark) {
        // Rose Dark Theme
        html.style.setProperty('--background', '350 40% 2%')
        html.style.setProperty('--foreground', '350 30% 92%')
        html.style.setProperty('--card', '350 40% 4%')
        html.style.setProperty('--card-foreground', '350 30% 92%')
        html.style.setProperty('--popover', '350 40% 4%')
        html.style.setProperty('--popover-foreground', '350 30% 92%')
        html.style.setProperty('--primary', '350 70% 65%')
        html.style.setProperty('--primary-foreground', '350 40% 2%')
        html.style.setProperty('--secondary', '350 30% 8%')
        html.style.setProperty('--secondary-foreground', '350 30% 92%')
        html.style.setProperty('--muted', '350 30% 6%')
        html.style.setProperty('--muted-foreground', '350 20% 50%')
        html.style.setProperty('--accent', '350 30% 10%')
        html.style.setProperty('--accent-foreground', '350 30% 92%')
        html.style.setProperty('--destructive', '0 84% 60%')
        html.style.setProperty('--destructive-foreground', '0 0% 100%')
        html.style.setProperty('--border', '350 30% 12%')
        html.style.setProperty('--input', '350 30% 6%')
        html.style.setProperty('--ring', '350 70% 65%')
      } else {
        // Rose Light Theme
        html.style.setProperty('--background', '350 40% 98%')
        html.style.setProperty('--foreground', '350 60% 8%')
        html.style.setProperty('--card', '350 40% 100%')
        html.style.setProperty('--card-foreground', '350 60% 8%')
        html.style.setProperty('--popover', '350 40% 100%')
        html.style.setProperty('--popover-foreground', '350 60% 8%')
        html.style.setProperty('--primary', '350 80% 50%')
        html.style.setProperty('--primary-foreground', '350 40% 98%')
        html.style.setProperty('--secondary', '350 40% 92%')
        html.style.setProperty('--secondary-foreground', '350 60% 8%')
        html.style.setProperty('--muted', '350 40% 95%')
        html.style.setProperty('--muted-foreground', '350 30% 40%')
        html.style.setProperty('--accent', '350 50% 90%')
        html.style.setProperty('--accent-foreground', '350 60% 8%')
        html.style.setProperty('--destructive', '0 84% 60%')
        html.style.setProperty('--destructive-foreground', '0 0% 100%')
        html.style.setProperty('--border', '350 30% 88%')
        html.style.setProperty('--input', '350 40% 95%')
        html.style.setProperty('--ring', '350 80% 50%')
      }
      html.classList.add('theme-rose')
    } else {
      // Default theme - remove custom properties to use CSS defaults
      const customProps = [
        '--background', '--foreground', '--card', '--card-foreground',
        '--popover', '--popover-foreground', '--primary', '--primary-foreground',
        '--secondary', '--secondary-foreground', '--muted', '--muted-foreground',
        '--accent', '--accent-foreground', '--destructive', '--destructive-foreground',
        '--border', '--input', '--ring'
      ]
      customProps.forEach(prop => html.style.removeProperty(prop))
    }
    
    // Save to localStorage
    localStorage.setItem("selected-theme", themeName)
  }, [theme]) // Add theme as dependency

  React.useEffect(() => {
    setMounted(true)
    // Load saved theme from localStorage
    const saved = localStorage.getItem("selected-theme") || "default"
    setSelectedTheme(saved)
    applyTheme(saved)
  }, [applyTheme])

  // Re-apply theme when light/dark mode changes
  React.useEffect(() => {
    if (mounted && selectedTheme !== "default") {
      applyTheme(selectedTheme)
    }
  }, [theme, mounted, selectedTheme, applyTheme])

  // Additional effect to watch for DOM class changes
  React.useEffect(() => {
    if (!mounted || selectedTheme === "default") return

    const html = document.documentElement
    let lastIsDark = html.classList.contains('dark')

    const checkAndReapply = () => {
      const currentIsDark = html.classList.contains('dark')
      if (currentIsDark !== lastIsDark) {
        lastIsDark = currentIsDark
        applyTheme(selectedTheme)
      }
    }

    // Check periodically for class changes
    const interval = setInterval(checkAndReapply, 500)

    return () => clearInterval(interval)
  }, [mounted, selectedTheme, applyTheme])

  const handleThemeChange = (themeName: string) => {
    setSelectedTheme(themeName)
    applyTheme(themeName)
  }

  if (!mounted) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className={cn("h-8 w-8 p-0", className)}
        >
          <Palette className="h-4 w-4" />
          <span className="sr-only">테마 선택</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={5} className="w-40">
        {themes.map((theme) => (
          <DropdownMenuItem
            key={theme.name}
            onClick={() => handleThemeChange(theme.name)}
            className="flex items-center gap-2 text-sm"
          >
            <div className={cn(
              "h-3 w-3 rounded-full border border-border/50",
              theme.color
            )} />
            <span className="flex-1">{theme.label}</span>
            {selectedTheme === theme.name && (
              <Check className="h-3 w-3" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}