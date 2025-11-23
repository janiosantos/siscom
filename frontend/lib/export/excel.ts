import * as XLSX from 'xlsx'

// Export any data to Excel
export function exportToExcel<T extends Record<string, any>>(
  data: T[],
  fileName: string,
  sheetName: string = 'Dados'
) {
  // Create workbook
  const workbook = XLSX.utils.book_new()

  // Create worksheet from data
  const worksheet = XLSX.utils.json_to_sheet(data)

  // Add worksheet to workbook
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)

  // Generate Excel file and download
  XLSX.writeFile(workbook, `${fileName}.xlsx`)
}

// Export data with custom headers
export function exportToExcelWithHeaders<T extends Record<string, any>>(
  data: T[],
  headers: Record<keyof T, string>,
  fileName: string,
  sheetName: string = 'Dados'
) {
  // Map data to use custom headers
  const mappedData = data.map((row) => {
    const newRow: Record<string, any> = {}
    Object.keys(headers).forEach((key) => {
      newRow[headers[key as keyof T]] = row[key]
    })
    return newRow
  })

  // Create workbook and worksheet
  const workbook = XLSX.utils.book_new()
  const worksheet = XLSX.utils.json_to_sheet(mappedData)

  // Auto-size columns
  const colWidths = Object.values(headers).map((header) => ({
    wch: Math.max(header.length, 15),
  }))
  worksheet['!cols'] = colWidths

  // Add worksheet to workbook
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)

  // Generate and download
  XLSX.writeFile(workbook, `${fileName}.xlsx`)
}

// Export multiple sheets
export function exportToExcelMultiSheet(
  sheets: Array<{
    data: any[]
    name: string
    headers?: Record<string, string>
  }>,
  fileName: string
) {
  const workbook = XLSX.utils.book_new()

  sheets.forEach(({ data, name, headers }) => {
    let worksheet: XLSX.WorkSheet

    if (headers) {
      const mappedData = data.map((row) => {
        const newRow: Record<string, any> = {}
        Object.keys(headers).forEach((key) => {
          newRow[headers[key]] = row[key]
        })
        return newRow
      })
      worksheet = XLSX.utils.json_to_sheet(mappedData)
    } else {
      worksheet = XLSX.utils.json_to_sheet(data)
    }

    XLSX.utils.book_append_sheet(workbook, worksheet, name)
  })

  XLSX.writeFile(workbook, `${fileName}.xlsx`)
}

// Export with formatting
export function exportToExcelFormatted<T extends Record<string, any>>(
  data: T[],
  headers: Record<keyof T, string>,
  fileName: string,
  options: {
    sheetName?: string
    currencyFields?: (keyof T)[]
    dateFields?: (keyof T)[]
    numberFields?: (keyof T)[]
  } = {}
) {
  const { sheetName = 'Dados', currencyFields = [], dateFields = [], numberFields = [] } = options

  // Map data with formatting
  const mappedData = data.map((row) => {
    const newRow: Record<string, any> = {}

    Object.keys(headers).forEach((key) => {
      const value = row[key]
      const headerName = headers[key as keyof T]

      // Format currency
      if (currencyFields.includes(key as keyof T) && typeof value === 'number') {
        newRow[headerName] = value.toLocaleString('pt-BR', {
          style: 'currency',
          currency: 'BRL',
        })
      }
      // Format date
      else if (dateFields.includes(key as keyof T)) {
        newRow[headerName] = value ? new Date(value).toLocaleDateString('pt-BR') : ''
      }
      // Format number
      else if (numberFields.includes(key as keyof T) && typeof value === 'number') {
        newRow[headerName] = value.toLocaleString('pt-BR')
      }
      // Default
      else {
        newRow[headerName] = value
      }
    })

    return newRow
  })

  const workbook = XLSX.utils.book_new()
  const worksheet = XLSX.utils.json_to_sheet(mappedData)

  // Auto-size columns
  const colWidths = Object.values(headers).map((header) => ({
    wch: Math.max(header.length + 2, 15),
  }))
  worksheet['!cols'] = colWidths

  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)
  XLSX.writeFile(workbook, `${fileName}.xlsx`)
}
