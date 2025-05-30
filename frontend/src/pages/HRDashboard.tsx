import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { Job, JobApplication } from "@/types/hr";
import JobPostForm from "@/components/hr/JobPostForm";
import JobsList from "@/components/hr/JobsList";
import ApplicationsList from "@/components/hr/ApplicationsList";

const HRDashboard = () => {
  const [activeTab, setActiveTab] = useState("add-job");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    if (user) {
      fetchJobs();
    }
  }, [user]);

  const fetchJobs = async () => {
    try {
      const { data, error } = await supabase
        .from("jobs")
        .select("*")
        .eq("hr_user_id", user?.id)
        .order("created_at", { ascending: false });

      if (error) throw error;
      setJobs(data || []);
    } catch (error: any) {
      console.error("Error fetching jobs:", error);
      toast({
        title: "Error",
        description: "Failed to fetch jobs",
        variant: "destructive",
      });
    }
  };

  const fetchApplicationsForJob = async (jobId: string) => {
    setLoading(true);
    try {
      // First get the applications
      const { data: applicationsData, error: applicationsError } =
        await supabase
          .from("job_applications")
          .select("*")
          .eq("job_id", jobId)
          .order("applied_at", { ascending: false });

      if (applicationsError) throw applicationsError;
      console.log("Applications data:", applicationsData);

      // Get all candidate profiles
      const candidateIds =
        applicationsData?.map((app) => app.candidate_id) || [];
      console.log("Candidate IDs:", candidateIds);

      const { data: profilesData, error: profilesError } = await supabase
        .from("profiles")
        .select("id, full_name, email")
        .in("id", candidateIds);

      if (profilesError) throw profilesError;
      console.log("Profiles data:", profilesData);

      // Create a map of profiles for easy lookup
      const profilesMap = new Map(
        profilesData?.map((profile) => [profile.id, profile]) || []
      );
      console.log("Profiles map:", Object.fromEntries(profilesMap));

      // Transform the data to match our interface
      const transformedData: JobApplication[] = (applicationsData || []).map(
        (app) => {
          const profile = profilesMap.get(app.candidate_id);
          console.log(
            "For candidate_id:",
            app.candidate_id,
            "Found profile:",
            profile
          );
          return {
            id: app.id,
            candidate_id: app.candidate_id,
            job_id: app.job_id,
            status: app.status,
            match_percentage: app.match_percentage || 0,
            skills: app.skills || "",
            experience_years: app.experience_years || 0,
            applied_at: app.applied_at,
            cover_letter: app.cover_letter,
            resume_url: app.resume_url,
            profiles: {
              full_name: profile?.full_name || "N/A",
              email: profile?.email || "N/A",
            },
          };
        }
      );

      console.log("Final transformed data:", transformedData);
      setApplications(transformedData);
      setSelectedJobId(jobId);
    } catch (error: any) {
      console.error("Error fetching applications:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to fetch applications",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const selectedJob = jobs.find((job) => job.id === selectedJobId) || null;

  const renderContent = () => {
    switch (activeTab) {
      case "add-job":
        return <JobPostForm onJobCreated={fetchJobs} />;

      case "status":
        return (
          <div className="space-y-8">
            <JobsList
              jobs={jobs}
              loading={false}
              onViewApplications={fetchApplicationsForJob}
            />

            {selectedJobId && (
              <ApplicationsList
                applications={applications}
                selectedJob={selectedJob}
                loading={loading}
              />
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar
        userType="hr"
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <div className="ml-64 p-8">{renderContent()}</div>
    </div>
  );
};

export default HRDashboard;
