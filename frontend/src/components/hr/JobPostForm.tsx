
import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';
import { JobFormData } from '@/types/hr';

interface JobPostFormProps {
  onJobCreated: () => void;
}

const JobPostForm: React.FC<JobPostFormProps> = ({ onJobCreated }) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [jobForm, setJobForm] = useState<JobFormData>({
    position: '',
    description: '',
    company: '',
    location: '',
    salary: '',
    last_date_to_apply: '',
    requirements: ''
  });

  const handleInputChange = (field: keyof JobFormData, value: string) => {
    setJobForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleJobSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      toast({
        title: "Error",
        description: "You must be logged in to post a job",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const { error } = await supabase
        .from('jobs')
        .insert([
          {
            position: jobForm.position,
            description: jobForm.description,
            company: jobForm.company,
            location: jobForm.location,
            salary: jobForm.salary,
            last_date_to_apply: jobForm.last_date_to_apply,
            requirements: jobForm.requirements,
            hr_user_id: user.id,
            is_active: true
          }
        ]);

      if (error) {
        console.error('Supabase error:', error);
        throw error;
      }

      toast({
        title: "Success!",
        description: "Job posted successfully and is now live!",
      });

      setJobForm({
        position: '',
        description: '',
        company: '',
        location: '',
        salary: '',
        last_date_to_apply: '',
        requirements: ''
      });

      onJobCreated();
    } catch (error: any) {
      console.error('Error posting job:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to post job. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Post a New Job</h2>
      
      <form onSubmit={handleJobSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Position *
            </label>
            <Input
              value={jobForm.position}
              onChange={(e) => handleInputChange('position', e.target.value)}
              placeholder="e.g. Frontend Developer"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company *
            </label>
            <Input
              value={jobForm.company}
              onChange={(e) => handleInputChange('company', e.target.value)}
              placeholder="Company name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location *
            </label>
            <Input
              value={jobForm.location}
              onChange={(e) => handleInputChange('location', e.target.value)}
              placeholder="e.g. San Francisco, CA or Remote"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Salary *
            </label>
            <Input
              value={jobForm.salary}
              onChange={(e) => handleInputChange('salary', e.target.value)}
              placeholder="e.g. $80,000 - $120,000"
              required
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Last Date to Apply *
            </label>
            <Input
              type="date"
              value={jobForm.last_date_to_apply}
              onChange={(e) => handleInputChange('last_date_to_apply', e.target.value)}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Job Description *
          </label>
          <Textarea
            value={jobForm.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            rows={6}
            placeholder="Detailed job description including responsibilities and qualifications..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Requirements
          </label>
          <Textarea
            value={jobForm.requirements}
            onChange={(e) => handleInputChange('requirements', e.target.value)}
            rows={4}
            placeholder="Specific requirements, technologies, years of experience, etc."
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition-all duration-200 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="h-5 w-5 mr-2" />
          {isSubmitting ? 'Posting Job...' : 'Post Job'}
        </button>
      </form>
    </div>
  );
};

export default JobPostForm;
