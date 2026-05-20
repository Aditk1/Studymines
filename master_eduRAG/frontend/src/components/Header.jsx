/**
 * Small branded header component used by legacy or focused layouts.
 */
export default function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-4xl font-bold text-blue-600">
          📚 Studymines
        </h1>
        <p className="text-gray-600 mt-2">
          AI-Powered Educational Summarization System
        </p>
      </div>
    </header>
  )
}
