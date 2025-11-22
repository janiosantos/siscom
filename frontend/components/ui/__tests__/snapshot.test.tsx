/**
 * Testes de Snapshot - Componentes UI
 *
 * Detecta mudanças não intencionais na estrutura de componentes
 */

import { render } from '@/__tests__/test-utils'
import { Button } from '../button'
import { Card } from '../card'
import { Input } from '../input'

describe('Button Snapshots', () => {
  it('should match default button snapshot', () => {
    const { container } = render(<Button>Click me</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match primary button snapshot', () => {
    const { container } = render(<Button variant="primary">Primary</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match secondary button snapshot', () => {
    const { container } = render(<Button variant="secondary">Secondary</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match outline button snapshot', () => {
    const { container } = render(<Button variant="outline">Outline</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match ghost button snapshot', () => {
    const { container } = render(<Button variant="ghost">Ghost</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match link button snapshot', () => {
    const { container } = render(<Button variant="link">Link</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match destructive button snapshot', () => {
    const { container } = render(<Button variant="destructive">Delete</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match disabled button snapshot', () => {
    const { container } = render(<Button disabled>Disabled</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match small button snapshot', () => {
    const { container } = render(<Button size="sm">Small</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match large button snapshot', () => {
    const { container } = render(<Button size="lg">Large</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match icon button snapshot', () => {
    const { container } = render(<Button size="icon">🔍</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match button with custom className', () => {
    const { container } = render(<Button className="custom-class">Custom</Button>)
    expect(container.firstChild).toMatchSnapshot()
  })
})

describe('Card Snapshots', () => {
  it('should match default card snapshot', () => {
    const { container } = render(
      <Card>
        <div>Card content</div>
      </Card>
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match card with header snapshot', () => {
    const { container } = render(
      <Card>
        <Card.Header>
          <Card.Title>Card Title</Card.Title>
        </Card.Header>
        <Card.Content>
          <p>Card content</p>
        </Card.Content>
      </Card>
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match card with description snapshot', () => {
    const { container } = render(
      <Card>
        <Card.Header>
          <Card.Title>Card Title</Card.Title>
          <Card.Description>Card description</Card.Description>
        </Card.Header>
      </Card>
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match card with footer snapshot', () => {
    const { container } = render(
      <Card>
        <Card.Content>
          <p>Card content</p>
        </Card.Content>
        <Card.Footer>
          <Button>Action</Button>
        </Card.Footer>
      </Card>
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match full card snapshot', () => {
    const { container } = render(
      <Card>
        <Card.Header>
          <Card.Title>Complete Card</Card.Title>
          <Card.Description>This is a complete card</Card.Description>
        </Card.Header>
        <Card.Content>
          <p>Card content goes here</p>
        </Card.Content>
        <Card.Footer>
          <Button variant="outline">Cancel</Button>
          <Button>Confirm</Button>
        </Card.Footer>
      </Card>
    )
    expect(container.firstChild).toMatchSnapshot()
  })
})

describe('Input Snapshots', () => {
  it('should match default input snapshot', () => {
    const { container } = render(<Input type="text" />)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match input with placeholder snapshot', () => {
    const { container } = render(<Input type="text" placeholder="Enter text" />)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match disabled input snapshot', () => {
    const { container } = render(<Input type="text" disabled />)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match email input snapshot', () => {
    const { container } = render(<Input type="email" />)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match password input snapshot', () => {
    const { container } = render(<Input type="password" />)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match number input snapshot', () => {
    const { container } = render(<Input type="number" />)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match input with error state', () => {
    const { container } = render(<Input type="text" className="error" />)
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match input with value snapshot', () => {
    const { container } = render(<Input type="text" value="Test value" readOnly />)
    expect(container.firstChild).toMatchSnapshot()
  })
})

describe('Form Component Snapshots', () => {
  it('should match login form snapshot', () => {
    const { container } = render(
      <form>
        <div className="space-y-4">
          <div>
            <label htmlFor="email">Email</label>
            <Input id="email" type="email" placeholder="email@example.com" />
          </div>
          <div>
            <label htmlFor="password">Password</label>
            <Input id="password" type="password" />
          </div>
          <Button type="submit" className="w-full">
            Login
          </Button>
        </div>
      </form>
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match product form snapshot', () => {
    const { container } = render(
      <form>
        <Card>
          <Card.Header>
            <Card.Title>Novo Produto</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            <div>
              <label htmlFor="codigo">Código</label>
              <Input id="codigo" type="text" />
            </div>
            <div>
              <label htmlFor="descricao">Descrição</label>
              <Input id="descricao" type="text" />
            </div>
            <div>
              <label htmlFor="preco">Preço</label>
              <Input id="preco" type="number" step="0.01" />
            </div>
          </Card.Content>
          <Card.Footer>
            <Button variant="outline">Cancelar</Button>
            <Button type="submit">Salvar</Button>
          </Card.Footer>
        </Card>
      </form>
    )
    expect(container.firstChild).toMatchSnapshot()
  })
})

describe('Complex Layout Snapshots', () => {
  it('should match dashboard card layout snapshot', () => {
    const { container } = render(
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <Card.Header>
            <Card.Title>Vendas Hoje</Card.Title>
          </Card.Header>
          <Card.Content>
            <p className="text-2xl font-bold">R$ 1.234,56</p>
          </Card.Content>
        </Card>
        <Card>
          <Card.Header>
            <Card.Title>Vendas Mês</Card.Title>
          </Card.Header>
          <Card.Content>
            <p className="text-2xl font-bold">R$ 45.678,90</p>
          </Card.Content>
        </Card>
        <Card>
          <Card.Header>
            <Card.Title>Produtos</Card.Title>
          </Card.Header>
          <Card.Content>
            <p className="text-2xl font-bold">1.234</p>
          </Card.Content>
        </Card>
        <Card>
          <Card.Header>
            <Card.Title>Clientes</Card.Title>
          </Card.Header>
          <Card.Content>
            <p className="text-2xl font-bold">567</p>
          </Card.Content>
        </Card>
      </div>
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match button group snapshot', () => {
    const { container } = render(
      <div className="flex gap-2">
        <Button variant="outline">Cancelar</Button>
        <Button variant="secondary">Salvar Rascunho</Button>
        <Button variant="primary">Publicar</Button>
      </div>
    )
    expect(container.firstChild).toMatchSnapshot()
  })

  it('should match toolbar snapshot', () => {
    const { container } = render(
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-xl font-bold">Produtos</h2>
        <div className="flex gap-2">
          <Input type="search" placeholder="Buscar..." className="w-64" />
          <Button variant="outline">Filtrar</Button>
          <Button>Novo Produto</Button>
        </div>
      </div>
    )
    expect(container.firstChild).toMatchSnapshot()
  })
})
