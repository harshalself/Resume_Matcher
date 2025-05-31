
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { resumeUrl, candidateName, jobId } = await req.json();
    
    console.log('Downloading resume for candidate:', candidateName);
    console.log('Resume URL:', resumeUrl);
    
    if (!resumeUrl || !candidateName) {
      throw new Error('Missing required parameters: resumeUrl and candidateName');
    }

    // Download the resume file
    const resumeResponse = await fetch(resumeUrl);
    if (!resumeResponse.ok) {
      throw new Error(`Failed to download resume: ${resumeResponse.statusText}`);
    }

    const resumeBlob = await resumeResponse.blob();
    const resumeArrayBuffer = await resumeBlob.arrayBuffer();
    
    // Create filename with candidate name
    const sanitizedName = candidateName.replace(/[^a-zA-Z0-9]/g, '_');
    const fileName = `${sanitizedName}_resume.pdf`;
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Create temp_resumes bucket if it doesn't exist
    const { error: bucketError } = await supabase.storage
      .createBucket('temp_resumes', { public: false });
    
    if (bucketError && !bucketError.message.includes('already exists')) {
      console.error('Error creating bucket:', bucketError);
    }

    // Upload to temp folder in storage
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('temp_resumes')
      .upload(`${jobId}/${fileName}`, resumeArrayBuffer, {
        contentType: 'application/pdf',
        upsert: true
      });

    if (uploadError) {
      console.error('Upload error:', uploadError);
      throw new Error(`Failed to store resume: ${uploadError.message}`);
    }

    console.log('Resume successfully stored:', uploadData);

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Resume downloaded and stored successfully',
        storedPath: uploadData.path
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('Error in download-resume function:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error.message || 'Unknown error occurred' 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    );
  }
});
