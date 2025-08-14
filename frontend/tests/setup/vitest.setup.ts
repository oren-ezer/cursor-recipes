import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
} as Storage

global.localStorage = localStorageMock

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Add CSS variables for Tailwind CSS
const style = document.createElement('style')
style.textContent = `
  :root {
    --background: 0 0% 100%;
    --foreground: 20 14.3% 4.1%;
    --card: 0 0% 100%;
    --card-foreground: 20 14.3% 4.1%;
    --popover: 0 0% 100%;
    --popover-foreground: 20 14.3% 4.1%;
    --primary: 24 9.8% 10%;
    --primary-foreground: 60 9.1% 97.8%;
    --secondary: 60 4.8% 95.9%;
    --secondary-foreground: 24 9.8% 10%;
    --muted: 60 4.8% 95.9%;
    --muted-foreground: 25 5.3% 44.7%;
    --accent: 60 4.8% 95.9%;
    --accent-foreground: 24 9.8% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 60 9.1% 97.8%;
    --border: 20 5.9% 90%;
    --input: 20 5.9% 90%;
    --ring: 20 14.3% 4.1%;
    --radius: 0.5rem;
  }
  
  /* Basic Tailwind-like utilities for testing */
  .space-y-6 > * + * {
    margin-top: 1.5rem;
  }
  
  .space-y-4 > * + * {
    margin-top: 1rem;
  }
  
  .space-y-2 > * + * {
    margin-top: 0.5rem;
  }
  
  .grid {
    display: grid;
  }
  
  .grid-cols-1 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
  
  .md\\:grid-cols-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  
  .md\\:grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .gap-4 {
    gap: 1rem;
  }
  
  .flex {
    display: flex;
  }
  
  .flex-1 {
    flex: 1 1 0%;
  }
  
  .flex-col {
    flex-direction: column;
  }
  
  .items-center {
    align-items: center;
  }
  
  .justify-between {
    justify-content: space-between;
  }
  
  .justify-center {
    justify-content: center;
  }
  
  .w-full {
    width: 100%;
  }
  
  .h-9 {
    height: 2.25rem;
  }
  
  .min-h-\\[80px\\] {
    min-height: 5rem;
  }
  
  .px-3 {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }
  
  .py-1 {
    padding-top: 0.25rem;
    padding-bottom: 0.25rem;
  }
  
  .py-2 {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
  }
  
  .rounded-md {
    border-radius: 0.375rem;
  }
  
  .border {
    border-width: 1px;
  }
  
  .border-input {
    border-color: hsl(var(--input));
  }
  
  .bg-background {
    background-color: hsl(var(--background));
  }
  
  .bg-transparent {
    background-color: transparent;
  }
  
  .text-sm {
    font-size: 0.875rem;
    line-height: 1.25rem;
  }
  
  .text-base {
    font-size: 1rem;
    line-height: 1.5rem;
  }
  
  .placeholder\\:text-muted-foreground::placeholder {
    color: hsl(var(--muted-foreground));
  }
  
  .focus-visible\\:outline-none:focus-visible {
    outline: 2px solid transparent;
    outline-offset: 2px;
  }
  
  .focus-visible\\:ring-1:focus-visible {
    --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);
    --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(1px + var(--tw-ring-offset-width)) var(--tw-ring-color);
    box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000);
  }
  
  .focus-visible\\:ring-ring:focus-visible {
    --tw-ring-color: hsl(var(--ring));
  }
  
  .disabled\\:cursor-not-allowed:disabled {
    cursor: not-allowed;
  }
  
  .disabled\\:opacity-50:disabled {
    opacity: 0.5;
  }
  
  .md\\:text-sm {
    font-size: 0.875rem;
    line-height: 1.25rem;
  }
  
  .ring-offset-background {
    --tw-ring-offset-color: hsl(var(--background));
  }
  
  .focus-visible\\:ring-2:focus-visible {
    --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);
    --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color);
    box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000);
  }
  
  .focus-visible\\:ring-offset-2:focus-visible {
    --tw-ring-offset-width: 2px;
  }
  
  .min-w-\\[8rem\\] {
    min-width: 8rem;
  }
  
  .max-h-96 {
    max-height: 24rem;
  }
  
  .overflow-hidden {
    overflow: hidden;
  }
  
  .bg-popover {
    background-color: hsl(var(--popover));
  }
  
  .text-popover-foreground {
    color: hsl(var(--popover-foreground));
  }
  
  .shadow-md {
    --tw-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --tw-shadow-colored: 0 4px 6px -1px var(--tw-shadow-color), 0 2px 4px -2px var(--tw-shadow-color);
    box-shadow: var(--tw-ring-offset-shadow, 0 0 #0000), var(--tw-ring-shadow, 0 0 #0000), var(--tw-shadow);
  }
  
  .z-50 {
    z-index: 50;
  }
  
  .relative {
    position: relative;
  }
  
  .absolute {
    position: absolute;
  }
  
  .left-2 {
    left: 0.5rem;
  }
  
  .right-2 {
    right: 0.5rem;
  }
  
  .top-2 {
    top: 0.5rem;
  }
  
  .bottom-2 {
    bottom: 0.5rem;
  }
  
  .h-3\\.5 {
    height: 0.875rem;
  }
  
  .w-3\\.5 {
    width: 0.875rem;
  }
  
  .pl-8 {
    padding-left: 2rem;
  }
  
  .pr-2 {
    padding-right: 0.5rem;
  }
  
  .py-1\\.5 {
    padding-top: 0.375rem;
    padding-bottom: 0.375rem;
  }
  
  .rounded-sm {
    border-radius: 0.125rem;
  }
  
  .cursor-default {
    cursor: default;
  }
  
  .select-none {
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
  }
  
  .outline-none {
    outline: 2px solid transparent;
    outline-offset: 2px;
  }
  
  .focus\\:bg-accent:focus {
    background-color: hsl(var(--accent));
  }
  
  .focus\\:text-accent-foreground:focus {
    color: hsl(var(--accent-foreground));
  }
  
  .data-\\[disabled\\]\\:pointer-events-none\\[data-disabled\\] {
    pointer-events: none;
  }
  
  .data-\\[disabled\\]\\:opacity-50\\[data-disabled\\] {
    opacity: 0.5;
  }
  
  .h-4 {
    height: 1rem;
  }
  
  .w-4 {
    width: 1rem;
  }
  
  .opacity-50 {
    opacity: 0.5;
  }
  
  .-mx-1 {
    margin-left: -0.25rem;
    margin-right: -0.25rem;
  }
  
  .my-1 {
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
  }
  
  .h-px {
    height: 1px;
  }
  
  .bg-muted {
    background-color: hsl(var(--muted));
  }
  
  .p-1 {
    padding: 0.25rem;
  }
  
  .p-6 {
    padding: 1.5rem;
  }
  
  .pt-0 {
    padding-top: 0px;
  }
  
  .space-y-1\\.5 > * + * {
    margin-top: 0.375rem;
  }
  
  .flex-col {
    flex-direction: column;
  }
  
  .font-semibold {
    font-weight: 600;
  }
  
  .leading-none {
    line-height: 1;
  }
  
  .tracking-tight {
    letter-spacing: -0.025em;
  }
  
  .text-center {
    text-align: center;
  }
  
  .text-destructive {
    color: hsl(var(--destructive));
  }
  
  .gap-4 {
    gap: 1rem;
  }
  
  .self-end {
    align-self: flex-end;
  }
  
  .rounded {
    border-radius: 0.25rem;
  }
  
  .text-gray-600 {
    color: rgb(75 85 99);
  }
  
  .dark\\:text-gray-400 {
    color: rgb(156 163 175);
  }
  
  .mt-2 {
    margin-top: 0.5rem;
  }
  
  .text-xs {
    font-size: 0.75rem;
    line-height: 1rem;
  }
  
  .text-lg {
    font-size: 1.125rem;
    line-height: 1.75rem;
  }
  
  .text-3xl {
    font-size: 1.875rem;
    line-height: 2.25rem;
  }
  
  .font-bold {
    font-weight: 700;
  }
  
  .text-gray-900 {
    color: rgb(17 24 39);
  }
  
  .dark\\:text-gray-100 {
    color: rgb(243 244 246);
  }
  
  .text-gray-300 {
    color: rgb(209 213 219);
  }
  
  .dark\\:text-gray-300 {
    color: rgb(209 213 219);
  }
  
  .text-gray-700 {
    color: rgb(55 65 81);
  }
  
  .dark\\:text-gray-700 {
    color: rgb(55 65 81);
  }
  
  .text-indigo-600 {
    color: rgb(79 70 229);
  }
  
  .dark\\:text-indigo-400 {
    color: rgb(129 140 248);
  }
  
  .hover\\:text-indigo-600:hover {
    color: rgb(79 70 229);
  }
  
  .dark\\:hover\\:text-indigo-400:hover {
    color: rgb(129 140 248);
  }
  
  .hover\\:bg-red-600:hover {
    background-color: rgb(220 38 38);
  }
  
  .bg-red-500 {
    background-color: rgb(239 68 68);
  }
  
  .bg-white {
    background-color: rgb(255 255 255);
  }
  
  .dark\\:bg-gray-800 {
    background-color: rgb(31 41 55);
  }
  
  .dark\\:bg-gray-900 {
    background-color: rgb(17 24 39);
  }
  
  .bg-gray-100 {
    background-color: rgb(243 244 246);
  }
  
  .shadow-md {
    --tw-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --tw-shadow-colored: 0 4px 6px -1px var(--tw-shadow-color), 0 2px 4px -2px var(--tw-shadow-color);
    box-shadow: var(--tw-ring-offset-shadow, 0 0 #0000), var(--tw-ring-shadow, 0 0 #0000), var(--tw-shadow);
  }
  
  .rounded-lg {
    border-radius: 0.5rem;
  }
  
  .px-4 {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  
  .py-6 {
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
  }
  
  .sm\\:px-6 {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }
  
  .mb-6 {
    margin-bottom: 1.5rem;
  }
  
  .mt-2 {
    margin-top: 0.5rem;
  }
  
  .max-w-7xl {
    max-width: 80rem;
  }
  
  .mx-auto {
    margin-left: auto;
    margin-right: auto;
  }
  
  .min-h-screen {
    min-height: 100vh;
  }
  
  .h-16 {
    height: 4rem;
  }
  
  .px-3 {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }
  
  .py-2 {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
  }
  
  .text-xl {
    font-size: 1.25rem;
    line-height: 1.75rem;
  }
  
  .space-x-4 > * + * {
    margin-left: 1rem;
  }
  
  .lg\\:px-8 {
    padding-left: 2rem;
    padding-right: 2rem;
  }
  
  .sm\\:px-0 {
    padding-left: 0px;
    padding-right: 0px;
  }
  
  .border-border {
    border-color: hsl(var(--border));
  }
  
  .bg-background {
    background-color: hsl(var(--background));
  }
  
  .text-foreground {
    color: hsl(var(--foreground));
  }
`
document.head.appendChild(style)
