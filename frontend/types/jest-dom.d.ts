import '@testing-library/jest-dom'

declare global {
  namespace jest {
    interface Matchers<R = void> {
      toBeInTheDocument(): R
      toHaveTextContent(text: string | RegExp): R
      toHaveValue(value: string | string[] | number): R
      toBeVisible(): R
      toBeDisabled(): R
      toBeEnabled(): R
      toHaveClass(...classNames: string[]): R
      toHaveAttribute(attr: string, value?: string): R
      toBeChecked(): R
      toBeEmptyDOMElement(): R
      toContainElement(element: HTMLElement | null): R
      toContainHTML(html: string): R
      toHaveDescription(text: string | RegExp): R
      toHaveFocus(): R
      toHaveFormValues(values: Record<string, any>): R
      toHaveStyle(css: string | Record<string, any>): R
      toBeInvalid(): R
      toBeRequired(): R
      toBeValid(): R
      toHaveAccessibleDescription(text: string | RegExp): R
      toHaveAccessibleName(text: string | RegExp): R
      toHaveDisplayValue(value: string | RegExp | Array<string | RegExp>): R
      toHaveErrorMessage(text: string | RegExp): R
    }
  }
}
