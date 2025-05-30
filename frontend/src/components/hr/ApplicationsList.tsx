import React from "react";
import { Job, JobApplication } from "@/types/hr";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Download } from "lucide-react";

interface ApplicationsListProps {
  applications: JobApplication[];
  selectedJob: Job | null;
  loading: boolean;
}

const ApplicationsList: React.FC<ApplicationsListProps> = ({
  applications,
  selectedJob,
  loading,
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <p className="text-center py-8">Loading applications...</p>
      </div>
    );
  }

  if (!selectedJob) {
    return null;
  }

  const getMatchColor = (match: number) => {
    if (match >= 80) return "text-green-600 bg-green-100";
    if (match >= 60) return "text-blue-600 bg-blue-100";
    if (match >= 40) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Applications for {selectedJob.position}
      </h2>

      {applications.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No applications yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[80px]">Sr. No.</TableHead>
                <TableHead>Candidate Name</TableHead>
                <TableHead>Match %</TableHead>
                <TableHead>Experience</TableHead>
                <TableHead>Skills</TableHead>
                <TableHead>Applied Date</TableHead>
                <TableHead>Resume</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {applications.map((application, index) => (
                <TableRow key={application.id}>
                  <TableCell>
                    <div className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold">
                      {index + 1}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-semibold">
                        {application.profiles.full_name}
                      </p>
                      <p className="text-sm text-gray-600">
                        {application.profiles.email}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-bold ${getMatchColor(
                        application.match_percentage
                      )}`}>
                      {application.match_percentage}%
                    </span>
                  </TableCell>
                  <TableCell>{application.experience_years} years</TableCell>
                  <TableCell>
                    <div className="max-w-xs">
                      <p className="text-sm truncate">
                        {application.skills || "Not provided"}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(application.applied_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {application.resume_url ? (
                      <a
                        href={application.resume_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-blue-600 hover:text-blue-800">
                        <Download className="h-4 w-4 mr-1" />
                        Download
                      </a>
                    ) : (
                      <span className="text-gray-500 text-sm">
                        Not provided
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};

export default ApplicationsList;
