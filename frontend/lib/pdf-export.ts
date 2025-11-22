import jsPDF from "jspdf"
import autoTable from "jspdf-autotable"

interface PDFColumn {
  header: string
  dataKey: string
}

interface PDFOptions {
  title: string
  subtitle?: string
  columns: PDFColumn[]
  data: any[]
  filename?: string
}

export function exportToPDF(options: PDFOptions) {
  const { title, subtitle, columns, data, filename = "relatorio.pdf" } = options

  // Create new PDF document
  const doc = new jsPDF()

  // Add title
  doc.setFontSize(18)
  doc.setFont("helvetica", "bold")
  doc.text(title, 14, 20)

  // Add subtitle if provided
  if (subtitle) {
    doc.setFontSize(11)
    doc.setFont("helvetica", "normal")
    doc.text(subtitle, 14, 28)
  }

  // Add date
  doc.setFontSize(9)
  doc.setTextColor(100)
  const date = new Date().toLocaleString("pt-BR")
  doc.text(`Gerado em: ${date}`, 14, subtitle ? 35 : 28)

  // Add table
  autoTable(doc, {
    startY: subtitle ? 40 : 33,
    head: [columns.map((col) => col.header)],
    body: data.map((row) => columns.map((col) => row[col.dataKey] ?? "")),
    styles: {
      fontSize: 9,
      cellPadding: 3,
    },
    headStyles: {
      fillColor: [59, 130, 246], // Blue
      textColor: [255, 255, 255],
      fontStyle: "bold",
    },
    alternateRowStyles: {
      fillColor: [245, 247, 250],
    },
    margin: { top: 10 },
  })

  // Add footer with page numbers
  const pageCount = (doc as any).internal.getNumberOfPages()
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i)
    doc.setFontSize(8)
    doc.setTextColor(150)
    doc.text(
      `Página ${i} de ${pageCount}`,
      doc.internal.pageSize.width / 2,
      doc.internal.pageSize.height - 10,
      { align: "center" }
    )
  }

  // Save the PDF
  doc.save(filename)
}

// Helper function for produtos export
export function exportProdutosToPDF(produtos: any[]) {
  exportToPDF({
    title: "Relatório de Produtos",
    subtitle: "Lista completa de produtos cadastrados",
    columns: [
      { header: "Código", dataKey: "codigo_barras" },
      { header: "Descrição", dataKey: "descricao" },
      { header: "Categoria", dataKey: "categoria_nome" },
      { header: "Preço Venda", dataKey: "preco_venda_formatted" },
      { header: "Estoque", dataKey: "estoque_atual" },
      { header: "Status", dataKey: "ativo_text" },
    ],
    data: produtos.map((p) => ({
      ...p,
      categoria_nome: p.categoria?.nome || "-",
      preco_venda_formatted: `R$ ${p.preco_venda.toFixed(2)}`,
      ativo_text: p.ativo ? "Ativo" : "Inativo",
    })),
    filename: `produtos_${new Date().toISOString().split("T")[0]}.pdf`,
  })
}

// Helper function for vendas export
export function exportVendasToPDF(vendas: any[]) {
  exportToPDF({
    title: "Relatório de Vendas",
    subtitle: "Registro de vendas realizadas",
    columns: [
      { header: "Número", dataKey: "numero" },
      { header: "Data", dataKey: "data_formatted" },
      { header: "Cliente", dataKey: "cliente_nome" },
      { header: "Total", dataKey: "total_formatted" },
      { header: "Status", dataKey: "status_text" },
    ],
    data: vendas.map((v) => ({
      ...v,
      numero: `#${v.id.toString().padStart(6, "0")}`,
      data_formatted: new Date(v.data_venda).toLocaleDateString("pt-BR"),
      cliente_nome: v.cliente?.nome || "Cliente Avulso",
      total_formatted: `R$ ${v.total_final.toFixed(2)}`,
      status_text:
        v.status.charAt(0).toUpperCase() + v.status.slice(1),
    })),
    filename: `vendas_${new Date().toISOString().split("T")[0]}.pdf`,
  })
}

// Helper function for estoque export
export function exportEstoqueToPDF(movimentacoes: any[]) {
  exportToPDF({
    title: "Relatório de Movimentações de Estoque",
    subtitle: "Histórico de entradas e saídas",
    columns: [
      { header: "Data", dataKey: "data_formatted" },
      { header: "Produto", dataKey: "produto_nome" },
      { header: "Tipo", dataKey: "tipo_text" },
      { header: "Quantidade", dataKey: "quantidade" },
      { header: "Observação", dataKey: "observacao" },
    ],
    data: movimentacoes.map((m) => ({
      ...m,
      data_formatted: new Date(m.data_movimentacao).toLocaleDateString(
        "pt-BR"
      ),
      produto_nome: m.produto?.descricao || "-",
      tipo_text: m.tipo.charAt(0).toUpperCase() + m.tipo.slice(1),
      observacao: m.observacao || "-",
    })),
    filename: `estoque_${new Date().toISOString().split("T")[0]}.pdf`,
  })
}

// Helper function for financeiro export
export function exportFinanceiroToPDF(contas: any[], tipo: "pagar" | "receber") {
  exportToPDF({
    title: `Relatório de Contas a ${tipo === "pagar" ? "Pagar" : "Receber"}`,
    subtitle: "Controle financeiro",
    columns: [
      { header: "Descrição", dataKey: "descricao" },
      { header: "Vencimento", dataKey: "vencimento_formatted" },
      { header: "Valor", dataKey: "valor_formatted" },
      { header: "Status", dataKey: "status_text" },
      { header: "Pagamento", dataKey: "pagamento_formatted" },
    ],
    data: contas.map((c) => ({
      ...c,
      vencimento_formatted: new Date(c.data_vencimento).toLocaleDateString(
        "pt-BR"
      ),
      valor_formatted: `R$ ${c.valor.toFixed(2)}`,
      status_text: c.status.charAt(0).toUpperCase() + c.status.slice(1),
      pagamento_formatted: c.data_pagamento
        ? new Date(c.data_pagamento).toLocaleDateString("pt-BR")
        : "-",
    })),
    filename: `contas_${tipo}_${new Date().toISOString().split("T")[0]}.pdf`,
  })
}
