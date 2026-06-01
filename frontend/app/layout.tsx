import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'spark — busca inteligente da produção científica',
  description: 'Busca textual e semântica da produção científica da UNEB',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
