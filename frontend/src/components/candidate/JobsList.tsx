import React, { useState, useEffect } from "react";
import { MapPin, DollarSign, Clock, Building, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { Job } from "@/types/hr";
import { useAuth } from "@/hooks/useAuth";

const JobsList: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [applyingJobs, setApplyingJobs] = useState<Set<string>>(new Set());
  const [appliedJobs, setAppliedJobs] = useState<Set<string>>(new Set());
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    fetchJobs();
    if (user) {
      fetchAppliedJobs();
    }
  }, [user]);

  const fetchJobs = async () => {
    try {
      console.log("Fetching jobs...");
      const { data, error } = await supabase
        .from("jobs")
        .select("*")
        .eq("is_active", true)
        .order("created_at", { ascending: false });

      if (error) {
        console.error("Supabase error:", error);
        throw error;
      }

      console.log("Fetched jobs:", data);
      setJobs(data || []);
    } catch (error: any) {
      console.error("Error fetching jobs:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to fetch job opportunities",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchAppliedJobs = async () => {
    try {
      const { data, error } = await supabase
        .from("job_applications")
        .select("job_id")
        .eq("candidate_id", user?.id);

      if (error) throw error;

      const appliedJobIds = new Set(data?.map((app) => app.job_id) || []);
      setAppliedJobs(appliedJobIds);
    } catch (error: any) {
      console.error("Error fetching applied jobs:", error);
    }
  };

  const downloadAndStoreResumeLocally = async (
    resumeUrl: string,
    candidateName: string,
    jobId: string
  ) => {
    try {
      console.log("Downloading resume from:", resumeUrl);

      // Call backend endpoint to download and store resume
      const response = await fetch(
        "http://localhost:5000/api/resume/download",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            resumeUrl,
            candidateName,
            jobId,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to download resume: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("Resume stored in backend temp folder:", result);
      return result.storageKey;
    } catch (error: any) {
      console.error("Error downloading and storing resume:", error);
      throw error;
    }
  };

  const handleApply = async (jobId: string) => {
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to apply for jobs",
        variant: "destructive",
      });
      return;
    }

    if (appliedJobs.has(jobId)) {
      toast({
        title: "Already Applied",
        description: "You have already applied for this position",
        variant: "default",
      });
      return;
    }

    setApplyingJobs((prev) => new Set(prev).add(jobId));

    try {
      // First get the candidate's profile to get their resume URL
      const { data: profileData, error: profileError } = await supabase
        .from("candidate_profiles")
        .select("resume_url, skills, experience_years, full_name")
        .eq("user_id", user.id)
        .single();

      if (profileError) {
        console.error("Error fetching profile:", profileError);
        throw profileError;
      }

      if (!profileData?.resume_url) {
        toast({
          title: "Resume Required",
          description:
            "Please upload your resume in your profile before applying",
          variant: "destructive",
        });
        setApplyingJobs((prev) => {
          const newSet = new Set(prev);
          newSet.delete(jobId);
          return newSet;
        });
        return;
      }

      // Download and store resume in local storage
      console.log("Starting resume download and local storage...");
      await downloadAndStoreResumeLocally(
        profileData.resume_url,
        profileData.full_name || user.email || "Unknown",
        jobId
      );

      // Insert the job application with resume URL
      const { error } = await supabase.from("job_applications").insert({
        job_id: jobId,
        candidate_id: user.id,
        status: "applied",
        applied_at: new Date().toISOString(),
        resume_url: profileData.resume_url,
        skills: profileData.skills,
        experience_years: profileData.experience_years,
      });

      if (error) throw error;

      // Add animation delay
      setTimeout(() => {
        setAppliedJobs((prev) => new Set(prev).add(jobId));
        setApplyingJobs((prev) => {
          const newSet = new Set(prev);
          newSet.delete(jobId);
          return newSet;
        });

        toast({
          title: "Success",
          description:
            "Application submitted successfully and resume stored locally",
          variant: "default",
        });
      }, 1000);
    } catch (error: any) {
      console.error("Error applying for job:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to submit application",
        variant: "destructive",
      });
      setApplyingJobs((prev) => {
        const newSet = new Set(prev);
        newSet.delete(jobId);
        return newSet;
      });
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <p className="text-center py-8">Loading job opportunities...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Job Opportunities
        </h2>

        {jobs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No job opportunities available at the moment.
          </p>
        ) : (
          <div className="grid gap-6">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow duration-200">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">
                      {job.position}
                    </h3>
                    <div className="flex items-center text-gray-600 mt-2">
                      <Building className="h-4 w-4 mr-2" />
                      {job.company}
                    </div>
                  </div>
                  <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                    {job.is_active ? "Active" : "Inactive"}
                  </span>
                </div>

                <div className="grid md:grid-cols-3 gap-4 mb-4">
                  <div className="flex items-center text-gray-600">
                    <MapPin className="h-4 w-4 mr-2" />
                    {job.location}
                  </div>
                  <div className="flex items-center text-gray-600">
                    <DollarSign className="h-4 w-4 mr-2" />
                    {job.salary}
                  </div>
                  <div className="flex items-center text-gray-600">
                    <Clock className="h-4 w-4 mr-2" />
                    Apply by:{" "}
                    {new Date(job.last_date_to_apply).toLocaleDateString()}
                  </div>
                </div>

                <p className="text-gray-700 mb-4">{job.description}</p>

                {job.requirements && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-900 mb-2">
                      Requirements:
                    </h4>
                    <p className="text-gray-700 text-sm">{job.requirements}</p>
                  </div>
                )}

                <button
                  onClick={() => handleApply(job.id)}
                  disabled={applyingJobs.has(job.id) || appliedJobs.has(job.id)}
                  className={`relative flex items-center justify-center px-6 py-2 rounded-lg font-semibold transition-all duration-200 ${
                    appliedJobs.has(job.id)
                      ? "bg-green-100 text-green-800 cursor-default"
                      : applyingJobs.has(job.id)
                      ? "bg-blue-100 text-blue-800 cursor-wait"
                      : "bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800"
                  }`}>
                  {applyingJobs.has(job.id) ? (
                    <span className="flex items-center">
                      <svg
                        className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-800"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Applying...
                    </span>
                  ) : appliedJobs.has(job.id) ? (
                    <span className="flex items-center">
                      <Check className="h-5 w-5 mr-2" />
                      Applied
                    </span>
                  ) : (
                    "Apply Now"
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default JobsList;
