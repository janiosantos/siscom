"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Warehouse,
  DollarSign,
  Users,
  FileText,
  Settings,
  Building2,
} from "lucide-react"
import { PermissionGuard } from "@/components/auth/permission-guard"

const menuItems = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    permission: undefined, // Available to all authenticated users
  },
  {
    title: "Vendas",
    href: "/dashboard/vendas",
    icon: ShoppingCart,
    permission: "vendas.view",
  },
  {
    title: "Produtos",
    href: "/dashboard/produtos",
    icon: Package,
    permission: "produtos.view",
  },
  {
    title: "Estoque",
    href: "/dashboard/estoque",
    icon: Warehouse,
    permission: "estoque.view",
  },
  {
    title: "Financeiro",
    href: "/dashboard/financeiro",
    icon: DollarSign,
    permission: "financeiro.view",
  },
  {
    title: "Clientes",
    href: "/dashboard/clientes",
    icon: Users,
    permission: "clientes.view",
  },
  {
    title: "Relatórios",
    href: "/dashboard/relatorios",
    icon: FileText,
    permission: "relatorios.view",
  },
  {
    title: "Configurações",
    href: "/dashboard/configuracoes",
    icon: Settings,
    permission: "configuracoes.view",
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden md:flex w-64 flex-col fixed inset-y-0 z-50 border-r bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Building2 className="h-6 w-6 text-primary" />
        <span className="ml-2 text-lg font-bold">ERP Siscom</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")

          const linkElement = (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.title}
            </Link>
          )

          // Wrap with PermissionGuard if permission is required
          if (item.permission) {
            return (
              <PermissionGuard key={item.href} permission={item.permission}>
                {linkElement}
              </PermissionGuard>
            )
          }

          // Dashboard and other items without permission are always visible
          return linkElement
        })}
      </nav>

      {/* Footer */}
      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground text-center">
          © 2025 ERP Siscom
        </p>
      </div>
    </aside>
  )
}
