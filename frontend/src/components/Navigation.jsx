export default function Navigation({ currentPage, setCurrentPage }) {
  const navItems = [
    { id: 'upload', label: 'Upload Document', icon: '📤' },
    { id: 'dashboard', label: 'My Dashboard', icon: '📊' },
    { id: 'leaderboard', label: 'Leaderboard', icon: '🏆' },
  ]

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex gap-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={`px-6 py-4 font-medium transition-colors ${
                currentPage === item.id
                  ? 'border-b-4 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {item.icon} {item.label}
            </button>
          ))}
        </div>
      </div>
    </nav>
  )
}
