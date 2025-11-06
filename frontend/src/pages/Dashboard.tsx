import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { clearTokens, getCurrentUser } from '@/lib/auth'

export default function Dashboard() {
  const navigate = useNavigate()
  const user = getCurrentUser()

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const response = await api.get('/api/v1/users/me')
      return response.data
    },
  })

  const handleLogout = () => {
    clearTokens()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between">
            <div className="flex">
              <div className="flex flex-shrink-0 items-center">
                <h1 className="text-xl font-bold">Full Stack Template</h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{user?.email}</span>
              <Button onClick={handleLogout} variant="outline" size="sm">
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="space-y-6">
          {/* Welcome Card */}
          <div className="rounded-lg bg-white p-6 shadow">
            <h2 className="text-2xl font-bold text-gray-900">
              Welcome, {profile?.full_name || user?.email}!
            </h2>
            <p className="mt-2 text-gray-600">
              This is your dashboard. Start building your application here.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-lg bg-white p-6 shadow">
              <div className="text-sm font-medium text-gray-500">Status</div>
              <div className="mt-2 text-3xl font-semibold text-gray-900">Active</div>
            </div>

            <div className="rounded-lg bg-white p-6 shadow">
              <div className="text-sm font-medium text-gray-500">Role</div>
              <div className="mt-2 text-3xl font-semibold text-gray-900">
                {user?.is_superuser ? 'Admin' : 'User'}
              </div>
            </div>

            <div className="rounded-lg bg-white p-6 shadow">
              <div className="text-sm font-medium text-gray-500">Email Verified</div>
              <div className="mt-2 text-3xl font-semibold text-gray-900">
                {user?.is_email_verified ? 'Yes' : 'No'}
              </div>
            </div>
          </div>

          {/* Features Section */}
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900">Features</h3>
            <ul className="mt-4 space-y-2 text-gray-600">
              <li>✅ FastAPI Backend with async/await</li>
              <li>✅ React 18 + TypeScript Frontend</li>
              <li>✅ JWT Authentication with refresh tokens</li>
              <li>✅ PostgreSQL Database with Alembic migrations</li>
              <li>✅ Redis Caching</li>
              <li>✅ Celery Background Tasks</li>
              <li>✅ Docker & Docker Compose</li>
              <li>✅ CI/CD with GitHub Actions</li>
              <li>✅ Kubernetes & Terraform ready</li>
              <li>✅ Prometheus & Grafana observability</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
}
