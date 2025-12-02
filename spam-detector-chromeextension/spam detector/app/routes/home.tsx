import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Spam Detector" },
    { name: "description", content: "Gmail Spam Detector Extension" },
  ];
}

export default function Home() {
  return (
    <div className="w-[350px] min-h-[400px] bg-gray-50 p-4 font-sans">
      <header className="flex items-center justify-between mb-6 border-b border-gray-200 pb-4">
        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <span className="text-2xl">🛡️</span> Spam Detector
        </h1>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span className="text-xs text-green-600 font-medium">Active</span>
        </div>
      </header>

      <main>
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4 border border-gray-100">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
            System Status
          </h2>
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Monitoring</span>
            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
              Enabled
            </span>
          </div>
          <div className="mt-3 flex items-center justify-between">
            <span className="text-gray-700">Backend API</span>
            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
              Connected
            </span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-100">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Recent Activity
          </h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded transition-colors">
              <div className="mt-1">
                <div className="w-2 h-2 rounded-full bg-red-500"></div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-800">
                  Suspicious Email
                </p>
                <p className="text-xs text-gray-500">Detected 2 mins ago</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded transition-colors">
              <div className="mt-1">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-800">Safe Email</p>
                <p className="text-xs text-gray-500">Detected 5 mins ago</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="mt-8 text-center text-xs text-gray-400">
        v1.0.0 • Powered by AI
      </footer>
    </div>
  );
}
