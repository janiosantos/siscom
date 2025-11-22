"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import {
  Calculator,
  Calendar,
  CreditCard,
  Settings,
  User,
  Package,
  ShoppingCart,
  Warehouse,
  DollarSign,
  Users,
  FileText,
  Search,
} from "lucide-react"
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"

export function CommandPalette() {
  const router = useRouter()
  const [open, setOpen] = React.useState(false)

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const runCommand = React.useCallback((command: () => void) => {
    setOpen(false)
    command()
  }, [])

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Buscar..." />
      <CommandList>
        <CommandEmpty>Nenhum resultado encontrado.</CommandEmpty>

        <CommandGroup heading="Navegação">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/dashboard"))}
          >
            <Calculator className="mr-2 h-4 w-4" />
            <span>Dashboard</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/produtos"))}
          >
            <Package className="mr-2 h-4 w-4" />
            <span>Produtos</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/vendas"))}
          >
            <ShoppingCart className="mr-2 h-4 w-4" />
            <span>Vendas</span>
          </CommandItem>
          <CommandItem onSelect={() => runCommand(() => router.push("/pdv"))}>
            <ShoppingCart className="mr-2 h-4 w-4" />
            <span>PDV (Ponto de Venda)</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/estoque"))}
          >
            <Warehouse className="mr-2 h-4 w-4" />
            <span>Estoque</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/financeiro"))}
          >
            <DollarSign className="mr-2 h-4 w-4" />
            <span>Financeiro</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/clientes"))}
          >
            <Users className="mr-2 h-4 w-4" />
            <span>Clientes</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/relatorios"))}
          >
            <FileText className="mr-2 h-4 w-4" />
            <span>Relatórios</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Ações Rápidas">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/produtos?new=true"))}
          >
            <Package className="mr-2 h-4 w-4" />
            <span>Novo Produto</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/pdv"))}
          >
            <ShoppingCart className="mr-2 h-4 w-4" />
            <span>Nova Venda</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/clientes?new=true"))}
          >
            <Users className="mr-2 h-4 w-4" />
            <span>Novo Cliente</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Configurações">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/configuracoes"))}
          >
            <Settings className="mr-2 h-4 w-4" />
            <span>Configurações</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/perfil"))}
          >
            <User className="mr-2 h-4 w-4" />
            <span>Perfil</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
