"use client"

import * as React from "react"
import { Moon, Sun, Settings, User, Shield } from "lucide-react"
import { useTheme } from "next-themes"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ThemeSelector } from "@/components/theme-selector"

interface HeaderProps {
  className?: string
}

export function Header({ className }: HeaderProps) {
  const { theme, setTheme } = useTheme()

  const handleGuardrailsAdmin = () => {
    // Open Guardrails Admin Panel in new tab
    window.open('http://localhost:3003', '_blank')
  }

  return (
    <header className={cn(
      "h-14 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
      "flex items-center justify-between px-6",
      className
    )}>
      {/* Logo/Brand */}
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 bg-primary rounded-md flex items-center justify-center">
          <span className="text-primary-foreground font-bold text-sm">S</span>
        </div>
        <div className="flex flex-col">
          <h1 className="text-base font-semibold tracking-tight leading-none">SDC Gen AI</h1>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        {/* Admin Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleGuardrailsAdmin}
          className="h-8 px-3 text-sm"
        >
          <Shield className="h-3 w-3 mr-2" />
          Admin
        </Button>
        
        {/* Color Theme Selector */}
        <ThemeSelector />
        
        {/* Dark/Light Mode Toggle */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">테마 변경</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={5}>
            <DropdownMenuItem onClick={() => setTheme("light")}>
              <Sun className="mr-2 h-3 w-3" />
              <span className="text-sm">라이트</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("dark")}>
              <Moon className="mr-2 h-3 w-3" />
              <span className="text-sm">다크</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("system")}>
              <Settings className="mr-2 h-3 w-3" />
              <span className="text-sm">시스템</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 px-2">
              <div className="w-5 h-5 bg-muted rounded-full flex items-center justify-center mr-1.5">
                <User className="h-3 w-3" />
              </div>
              <span className="text-sm font-medium">사용자</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={5}>
            <DropdownMenuItem className="text-sm">프로필</DropdownMenuItem>
            <DropdownMenuItem className="text-sm">설정</DropdownMenuItem>
            <DropdownMenuItem 
              className="text-sm cursor-pointer"
              onClick={handleGuardrailsAdmin}
            >
              <Shield className="mr-2 h-3 w-3" />
              Admin
            </DropdownMenuItem>
            <DropdownMenuItem className="text-sm">로그아웃</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}