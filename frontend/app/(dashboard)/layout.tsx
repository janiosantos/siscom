"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/navigation/sidebar"
import { Header } from "@/components/navigation/header"
import { CommandPalette } from "@/components/command-palette"
import { useUserStore } from "@/lib/store/user"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const { user, setUser } = useUserStore()

  useEffect(() => {
    // Check if user is authenticated
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token")
      const storedUser = localStorage.getItem("user")

      if (!token) {
        router.push("/login")
        return
      }

      // Set user from localStorage if not in store
      if (!user && storedUser) {
        try {
          setUser(JSON.parse(storedUser))
        } catch (error) {
          console.error("Error parsing user:", error)
          router.push("/login")
        }
      }
    }
  }, [user, setUser, router])

  return (
    <div className="min-h-screen bg-background">
      <CommandPalette />
      <Sidebar />
      <div className="md:pl-64">
        <Header />
        <main className="p-6">{children}</main>
      </div>
    </div>
  )
}
