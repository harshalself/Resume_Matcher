
import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import ProfileForm from '../components/candidate/ProfileForm';
import JobsList from '../components/candidate/JobsList';

const CandidateDashboard = () => {
  const [activeTab, setActiveTab] = useState('profile');

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return <ProfileForm />;
      case 'jobs':
        return <JobsList />;
      default:
        return <ProfileForm />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar userType="candidate" activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <div className="ml-64 p-8">
        {renderContent()}
      </div>
    </div>
  );
};

export default CandidateDashboard;
