// Export any data to CSV
export function exportToCSV<T extends Record<string, any>>(
  data: T[],
  fileName: string,
  delimiter: string = ','
) {
  if (data.length === 0) {
    console.warn('No data to export')
    return
  }

  // Get headers from first object
  const headers = Object.keys(data[0])

  // Create CSV content
  const csvContent = [
    // Header row
    headers.join(delimiter),
    // Data rows
    ...data.map((row) =>
      headers
        .map((header) => {
          const value = row[header]
          // Escape quotes and wrap in quotes if contains delimiter
          const stringValue = value?.toString() ?? ''
          if (stringValue.includes(delimiter) || stringValue.includes('"') || stringValue.includes('\n')) {
            return `"${stringValue.replace(/"/g, '""')}"`
          }
          return stringValue
        })
        .join(delimiter)
    ),
  ].join('\n')

  // Create Blob and download
  downloadCSV(csvContent, fileName)
}

// Export with custom headers
export function exportToCSVWithHeaders<T extends Record<string, any>>(
  data: T[],
  headers: Record<keyof T, string>,
  fileName: string,
  delimiter: string = ','
) {
  if (data.length === 0) {
    console.warn('No data to export')
    return
  }

  const headerKeys = Object.keys(headers) as (keyof T)[]
  const headerValues = headerKeys.map((key) => headers[key])

  // Create CSV content
  const csvContent = [
    // Header row
    headerValues.join(delimiter),
    // Data rows
    ...data.map((row) =>
      headerKeys
        .map((key) => {
          const value = row[key]
          const stringValue = value?.toString() ?? ''
          if (stringValue.includes(delimiter) || stringValue.includes('"') || stringValue.includes('\n')) {
            return `"${stringValue.replace(/"/g, '""')}"`
          }
          return stringValue
        })
        .join(delimiter)
    ),
  ].join('\n')

  downloadCSV(csvContent, fileName)
}

// Export with formatting
export function exportToCSVFormatted<T extends Record<string, any>>(
  data: T[],
  headers: Record<keyof T, string>,
  fileName: string,
  options: {
    delimiter?: string
    currencyFields?: (keyof T)[]
    dateFields?: (keyof T)[]
    numberFields?: (keyof T)[]
  } = {}
) {
  if (data.length === 0) {
    console.warn('No data to export')
    return
  }

  const {
    delimiter = ',',
    currencyFields = [],
    dateFields = [],
    numberFields = [],
  } = options

  const headerKeys = Object.keys(headers) as (keyof T)[]
  const headerValues = headerKeys.map((key) => headers[key])

  // Map data with formatting
  const formattedData = data.map((row) => {
    const formattedRow: Record<string, string> = {}

    headerKeys.forEach((key) => {
      const value = row[key]

      // Format currency
      if (currencyFields.includes(key) && typeof value === 'number') {
        formattedRow[key as string] = value.toLocaleString('pt-BR', {
          style: 'currency',
          currency: 'BRL',
        })
      }
      // Format date
      else if (dateFields.includes(key)) {
        formattedRow[key as string] = value
          ? new Date(value).toLocaleDateString('pt-BR')
          : ''
      }
      // Format number
      else if (numberFields.includes(key) && typeof value === 'number') {
        formattedRow[key as string] = value.toLocaleString('pt-BR')
      }
      // Default
      else {
        formattedRow[key as string] = value?.toString() ?? ''
      }
    })

    return formattedRow
  })

  // Create CSV content
  const csvContent = [
    // Header row
    headerValues.join(delimiter),
    // Data rows
    ...formattedData.map((row) =>
      headerKeys
        .map((key) => {
          const value = row[key as string]
          if (value.includes(delimiter) || value.includes('"') || value.includes('\n')) {
            return `"${value.replace(/"/g, '""')}"`
          }
          return value
        })
        .join(delimiter)
    ),
  ].join('\n')

  downloadCSV(csvContent, fileName)
}

// Helper function to download CSV
function downloadCSV(csvContent: string, fileName: string) {
  // Add BOM for Excel UTF-8 recognition
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })

  // Create download link
  const link = document.createElement('a')
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `${fileName}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }
}
