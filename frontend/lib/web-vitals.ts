/**
 * Web Vitals Tracking
 *
 * Monitora Core Web Vitals automaticamente
 */

import React from 'react'
import { onCLS, onFCP, onINP, onLCP, onTTFB, Metric } from 'web-vitals'

// Tipos de métricas
type WebVitalsMetric = {
  id: string
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  delta: number
  navigationType: string
}

// Thresholds baseados em Google recommendations
const THRESHOLDS = {
  CLS: { good: 0.1, poor: 0.25 },
  FCP: { good: 1800, poor: 3000 },
  INP: { good: 200, poor: 500 },
  LCP: { good: 2500, poor: 4000 },
  TTFB: { good: 800, poor: 1800 },
}

// Função para determinar rating
function getRating(metricName: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const thresholds = THRESHOLDS[metricName as keyof typeof THRESHOLDS]
  if (!thresholds) return 'good'

  if (value <= thresholds.good) return 'good'
  if (value <= thresholds.poor) return 'needs-improvement'
  return 'poor'
}

// Função para enviar para analytics
function sendToAnalytics(metric: WebVitalsMetric) {
  // Google Analytics 4
  if (typeof window !== 'undefined' && (window as any).gtag) {
    ;(window as any).gtag('event', metric.name, {
      value: Math.round(metric.value),
      event_category: 'Web Vitals',
      event_label: metric.id,
      non_interaction: true,
    })
  }

  // Console (desenvolvimento)
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Web Vitals] ${metric.name}:`, {
      value: metric.value.toFixed(2),
      rating: metric.rating,
      delta: metric.delta.toFixed(2),
    })
  }

  // Custom analytics endpoint (opcional)
  if (process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT) {
    fetch(process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        metric: metric.name,
        value: metric.value,
        rating: metric.rating,
        page: window.location.pathname,
        timestamp: new Date().toISOString(),
      }),
      keepalive: true,
    }).catch(console.error)
  }
}

// Função de callback para métricas
function handleMetric(metric: Metric) {
  const webVitalsMetric: WebVitalsMetric = {
    id: metric.id,
    name: metric.name,
    value: metric.value,
    rating: getRating(metric.name, metric.value),
    delta: metric.delta,
    navigationType: (metric as any).navigationType || 'unknown',
  }

  sendToAnalytics(webVitalsMetric)

  // Armazenar em localStorage (opcional)
  if (typeof window !== 'undefined' && window.localStorage) {
    const key = `webvitals_${metric.name}`
    const stored = JSON.parse(window.localStorage.getItem('webvitals') || '{}')
    stored[key] = webVitalsMetric
    window.localStorage.setItem('webvitals', JSON.stringify(stored))
  }
}

// Inicializar tracking de Web Vitals
export function initWebVitals() {
  try {
    onCLS(handleMetric)
    onFCP(handleMetric)
    onINP(handleMetric)
    onLCP(handleMetric)
    onTTFB(handleMetric)
  } catch (error) {
    console.error('Failed to initialize Web Vitals:', error)
  }
}

// Hook para Next.js
export function reportWebVitals(metric: Metric) {
  handleMetric(metric)
}

// Função para obter métricas do localStorage
export function getStoredWebVitals(): Record<string, WebVitalsMetric> {
  if (typeof window === 'undefined' || !window.localStorage) {
    return {}
  }

  try {
    return JSON.parse(window.localStorage.getItem('webvitals') || '{}')
  } catch {
    return {}
  }
}

// Função para limpar métricas
export function clearWebVitals() {
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.removeItem('webvitals')
  }
}

// Componente React para exibir Web Vitals (DEV apenas)
export function WebVitalsDebugger(): React.ReactElement | null {
  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  const [vitals, setVitals] = React.useState<Record<string, WebVitalsMetric>>({})

  React.useEffect(() => {
    // Atualizar a cada 2 segundos
    const interval = setInterval(() => {
      setVitals(getStoredWebVitals())
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  if (Object.keys(vitals).length === 0) {
    return null
  }

  const containerStyle: React.CSSProperties = {
    position: 'fixed',
    bottom: 20,
    right: 20,
    background: 'rgba(0, 0, 0, 0.9)',
    color: 'white',
    padding: '10px 15px',
    borderRadius: 8,
    fontSize: 12,
    fontFamily: 'monospace',
    zIndex: 9999,
    maxWidth: 300,
  }

  const titleStyle: React.CSSProperties = {
    fontWeight: 'bold',
    marginBottom: 8,
  }

  const metricRowStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: 4,
  }

  const buttonStyle: React.CSSProperties = {
    marginTop: 8,
    padding: '4px 8px',
    background: '#333',
    border: '1px solid #666',
    color: 'white',
    borderRadius: 4,
    cursor: 'pointer',
    fontSize: 11,
  }

  const getMetricColor = (rating: string): string => {
    if (rating === 'good') return '#0f0'
    if (rating === 'needs-improvement') return '#ff0'
    return '#f00'
  }

  return React.createElement(
    'div',
    { style: containerStyle },
    React.createElement('div', { style: titleStyle }, 'Web Vitals'),
    ...Object.entries(vitals).map(([key, metric]) =>
      React.createElement(
        'div',
        { key, style: metricRowStyle },
        React.createElement('span', null, `${metric.name}:`),
        React.createElement(
          'span',
          {
            style: {
              color: getMetricColor(metric.rating),
              fontWeight: 'bold',
            },
          },
          `${metric.value.toFixed(0)} (${metric.rating})`
        )
      )
    ),
    React.createElement(
      'button',
      { onClick: clearWebVitals, style: buttonStyle },
      'Clear'
    )
  )
}
