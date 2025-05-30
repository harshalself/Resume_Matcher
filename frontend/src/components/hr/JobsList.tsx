
import React from 'react';
import { Users, Eye, MapPin, DollarSign, Calendar } from 'lucide-react';
import { Job } from '@/types/hr';

interface JobsListProps {
  jobs: Job[];
  loading: boolean;
  onViewApplications: (jobId: string) => void;
}

const JobsList: React.FC<JobsListProps> = ({ jobs, loading, onViewApplications }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <p className="text-center py-8">Loading jobs...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Job Postings Overview</h2>
      
      {jobs.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No jobs posted yet.</p>
      ) : (
        <div className="grid gap-6">
          {jobs.map((job) => (
            <div key={job.id} className="border border-gray-200 rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{job.position}</h3>
                  <p className="text-gray-600 mb-2">{job.company}</p>
                  <div className="flex items-center text-gray-600 mt-2 space-x-4">
                    <div className="flex items-center">
                      <MapPin className="h-4 w-4 mr-1" />
                      {job.location}
                    </div>
                    <div className="flex items-center">
                      <DollarSign className="h-4 w-4 mr-1" />
                      {job.salary}
                    </div>
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1" />
                      Apply by: {new Date(job.last_date_to_apply).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  job.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {job.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center text-gray-600">
                  <Users className="h-5 w-5 mr-2" />
                  <span>View applications</span>
                </div>
                
                <button 
                  onClick={() => onViewApplications(job.id)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors duration-200 flex items-center"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View Applications
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JobsList;
