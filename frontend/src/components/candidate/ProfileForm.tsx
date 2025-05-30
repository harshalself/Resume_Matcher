import React, { useState, useEffect } from "react";
import { Upload } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";

interface ProfileData {
  full_name: string;
  phone: string;
  experience_years: number;
  education: string;
  skills: string;
  resume_url: string | null;
}

const ProfileForm: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);

  const [profileData, setProfileData] = useState<ProfileData>({
    full_name: "",
    phone: "",
    experience_years: 0,
    education: "",
    skills: "",
    resume_url: null,
  });

  useEffect(() => {
    if (user) {
      fetchProfile();
    }
  }, [user]);

  const fetchProfile = async () => {
    if (!user) return;

    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from("candidate_profiles")
        .select("*")
        .eq("user_id", user.id)
        .single();

      if (error && error.code !== "PGRST116") {
        throw error;
      }

      if (data) {
        setProfileData({
          full_name: data.full_name || "",
          phone: data.phone || "",
          experience_years: data.experience_years || 0,
          education: data.education || "",
          skills: data.skills || "",
          resume_url: data.resume_url,
        });
      }
    } catch (error: any) {
      console.error("Error fetching profile:", error);
      toast({
        title: "Error",
        description: "Failed to load profile data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (
    field: keyof ProfileData,
    value: string | number
  ) => {
    setProfileData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleResumeUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file || !user) return;

    // Check file type
    if (
      ![
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ].includes(file.type)
    ) {
      toast({
        title: "Error",
        description: "Please upload a PDF or Word document",
        variant: "destructive",
      });
      return;
    }

    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: "Error",
        description: "File size should be less than 10MB",
        variant: "destructive",
      });
      return;
    }

    setUploadingResume(true);
    try {
      // Delete old resume if exists
      if (profileData.resume_url) {
        const oldPath = profileData.resume_url.split("/").pop();
        if (oldPath) {
          const { error: deleteError } = await supabase.storage
            .from("resumes")
            .remove([`${user.id}/${oldPath}`]);

          if (deleteError) {
            console.error("Error deleting old resume:", deleteError);
          }
        }
      }

      // Upload new resume
      const fileExt = file.name.split(".").pop();
      const fileName = `${user.id}/${Date.now()}.${fileExt}`;

      console.log("Uploading resume:", {
        fileName,
        fileType: file.type,
        fileSize: file.size,
      });

      const { data: uploadData, error: uploadError } = await supabase.storage
        .from("resumes")
        .upload(fileName, file, {
          cacheControl: "3600",
          upsert: true,
        });

      if (uploadError) {
        console.error("Upload error:", uploadError);
        throw uploadError;
      }

      console.log("Upload successful:", uploadData);

      // Get public URL
      const {
        data: { publicUrl },
      } = supabase.storage.from("resumes").getPublicUrl(fileName);

      console.log("Public URL:", publicUrl);

      // Update profile with new resume URL
      setProfileData((prev) => ({
        ...prev,
        resume_url: publicUrl,
      }));

      // Update resume_url in job_applications table
      const { error: updateError } = await supabase
        .from("job_applications")
        .update({ resume_url: publicUrl })
        .eq("candidate_id", user.id);

      if (updateError) {
        console.error("Error updating job applications:", updateError);
        throw updateError;
      }

      toast({
        title: "Success!",
        description: "Resume uploaded and updated successfully!",
      });
    } catch (error: any) {
      console.error("Error uploading resume:", error);
      toast({
        title: "Error",
        description:
          error.message || "Failed to upload resume. Please try again.",
        variant: "destructive",
      });
    } finally {
      setUploadingResume(false);
    }
  };

  const handleSaveChanges = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setIsSaving(true);
    try {
      const { error } = await supabase.from("candidate_profiles").upsert(
        {
          user_id: user.id,
          full_name: profileData.full_name,
          phone: profileData.phone,
          experience_years: profileData.experience_years,
          education: profileData.education,
          skills: profileData.skills,
          resume_url: profileData.resume_url,
          updated_at: new Date().toISOString(),
        },
        {
          onConflict: "user_id",
        }
      );

      if (error) throw error;

      toast({
        title: "Success!",
        description: "Profile updated successfully!",
      });
    } catch (error: any) {
      console.error("Error saving profile:", error);
      toast({
        title: "Error",
        description: "Failed to save profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <p className="text-center py-8">Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">My Profile</h2>

      <form onSubmit={handleSaveChanges} className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Full Name *
            </label>
            <Input
              type="text"
              value={profileData.full_name}
              onChange={(e) => handleInputChange("full_name", e.target.value)}
              placeholder="Enter your full name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <Input
              type="email"
              value={user?.email || ""}
              disabled
              className="bg-gray-100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone Number
            </label>
            <Input
              type="tel"
              value={profileData.phone}
              onChange={(e) => handleInputChange("phone", e.target.value)}
              placeholder="+1 (555) 123-4567"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Years of Experience *
            </label>
            <Input
              type="number"
              value={profileData.experience_years}
              onChange={(e) =>
                handleInputChange(
                  "experience_years",
                  parseInt(e.target.value) || 0
                )
              }
              min="0"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Education
          </label>
          <Textarea
            value={profileData.education}
            onChange={(e) => handleInputChange("education", e.target.value)}
            rows={3}
            placeholder="e.g. Computer Science, Stanford University"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Skills *
          </label>
          <Textarea
            value={profileData.skills}
            onChange={(e) => handleInputChange("skills", e.target.value)}
            rows={3}
            placeholder="e.g., React, Node.js, Python, AWS"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Resume
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors duration-200">
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleResumeUpload}
              className="hidden"
              id="resume-upload"
              disabled={uploadingResume}
            />
            <label htmlFor="resume-upload" className="cursor-pointer block">
              <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">
                {uploadingResume
                  ? "Uploading..."
                  : "Click to upload or drag and drop"}
              </p>
              <p className="text-sm text-gray-500">PDF, DOC up to 10MB</p>
              {profileData.resume_url && (
                <p className="text-sm text-green-600 mt-2">
                  Resume uploaded successfully!
                </p>
              )}
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSaving}
          className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed">
          {isSaving ? "Saving Changes..." : "Save Changes"}
        </button>
      </form>
    </div>
  );
};

export default ProfileForm;
