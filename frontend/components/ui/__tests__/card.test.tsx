import React from 'react'
import { render, screen } from '@/__tests__/test-utils'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../card'

describe('Card Components', () => {
  describe('Card', () => {
    it('should render correctly', () => {
      render(
        <Card data-testid="card">
          <div>Card Content</div>
        </Card>
      )

      const card = screen.getByTestId('card')
      expect(card).toBeInTheDocument()
      expect(card).toHaveClass('rounded-lg', 'border', 'bg-card')
    })

    it('should apply custom className', () => {
      render(
        <Card className="custom-card" data-testid="card">
          Content
        </Card>
      )

      expect(screen.getByTestId('card')).toHaveClass('custom-card')
    })
  })

  describe('CardHeader', () => {
    it('should render correctly', () => {
      render(
        <Card>
          <CardHeader data-testid="header">
            <CardTitle>Title</CardTitle>
          </CardHeader>
        </Card>
      )

      const header = screen.getByTestId('header')
      expect(header).toBeInTheDocument()
      expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5')
    })
  })

  describe('CardTitle', () => {
    it('should render title with correct styles', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>My Card Title</CardTitle>
          </CardHeader>
        </Card>
      )

      const title = screen.getByText('My Card Title')
      expect(title).toBeInTheDocument()
      expect(title).toHaveClass('text-2xl', 'font-semibold')
    })
  })

  describe('CardDescription', () => {
    it('should render description with correct styles', () => {
      render(
        <Card>
          <CardHeader>
            <CardDescription>Card description text</CardDescription>
          </CardHeader>
        </Card>
      )

      const description = screen.getByText('Card description text')
      expect(description).toBeInTheDocument()
      expect(description).toHaveClass('text-sm', 'text-muted-foreground')
    })
  })

  describe('CardContent', () => {
    it('should render content correctly', () => {
      render(
        <Card>
          <CardContent data-testid="content">
            <p>Card body content</p>
          </CardContent>
        </Card>
      )

      const content = screen.getByTestId('content')
      expect(content).toBeInTheDocument()
      expect(content).toHaveClass('p-6', 'pt-0')
      expect(screen.getByText('Card body content')).toBeInTheDocument()
    })
  })

  describe('CardFooter', () => {
    it('should render footer correctly', () => {
      render(
        <Card>
          <CardFooter data-testid="footer">
            <button>Action</button>
          </CardFooter>
        </Card>
      )

      const footer = screen.getByTestId('footer')
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-0')
    })
  })

  describe('Complete Card', () => {
    it('should render a complete card with all parts', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Complete Card</CardTitle>
            <CardDescription>This is a complete card example</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Main content goes here</p>
          </CardContent>
          <CardFooter>
            <button>Submit</button>
          </CardFooter>
        </Card>
      )

      expect(screen.getByText('Complete Card')).toBeInTheDocument()
      expect(screen.getByText('This is a complete card example')).toBeInTheDocument()
      expect(screen.getByText('Main content goes here')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
    })
  })
})
