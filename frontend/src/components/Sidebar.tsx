
import React from 'react';
import { User, Briefcase, BarChart, Plus, LogOut } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

interface SidebarProps {
  userType: 'candidate' | 'hr';
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ userType, activeTab, setActiveTab }) => {
  const { signOut, user } = useAuth();

  const candidateMenuItems = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'jobs', label: 'Job Opportunities', icon: Briefcase }
  ];

  const hrMenuItems = [
    { id: 'add-job', label: 'Add Job', icon: Plus },
    { id: 'status', label: 'Job Status & Candidates', icon: BarChart }
  ];

  const menuItems = userType === 'candidate' ? candidateMenuItems : hrMenuItems;

  const handleSignOut = async () => {
    await signOut();
  };

  const userName = user?.user_metadata?.full_name || user?.email || 'User';

  return (
    <div className="bg-white shadow-lg h-screen w-64 fixed left-0 top-0 z-40">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-900">
          {userType === 'candidate' ? 'Candidate' : 'HR'} Dashboard
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Welcome back, {userName}
        </p>
      </div>

      <nav className="mt-6">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center px-6 py-3 text-left hover:bg-blue-50 transition-colors duration-200 ${
              activeTab === item.id
                ? 'bg-blue-50 text-blue-600 border-r-2 border-blue-600'
                : 'text-gray-700 hover:text-blue-600'
            }`}
          >
            <item.icon className="h-5 w-5 mr-3" />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="absolute bottom-6 w-full px-6">
        <button 
          onClick={handleSignOut}
          className="w-full flex items-center px-4 py-3 text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200"
        >
          <LogOut className="h-5 w-5 mr-3" />
          Sign Out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
