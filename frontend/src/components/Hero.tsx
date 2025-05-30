
import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowDown, CheckCircle, Users, Target } from 'lucide-react';

const Hero = () => {
  return (
    <div className="relative bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen flex items-center">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-indigo-600/10"></div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="text-center lg:text-left">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 leading-tight">
              Transform Your
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600"> Recruitment </span>
              Process
            </h1>
            
            <p className="mt-6 text-xl text-gray-600 leading-relaxed">
              RecruitMate connects top talent with leading companies through intelligent matching, 
              streamlined workflows, and data-driven insights.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Link
                to="/auth"
                className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Get Started Today
              </Link>
              <button className="border-2 border-blue-600 text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-50 transition-all duration-200">
                Watch Demo
              </button>
            </div>

            {/* Stats */}
            <div className="mt-12 grid grid-cols-3 gap-6">
              <div className="text-center lg:text-left">
                <div className="text-3xl font-bold text-blue-600">500+</div>
                <div className="text-sm text-gray-600">Companies</div>
              </div>
              <div className="text-center lg:text-left">
                <div className="text-3xl font-bold text-blue-600">50K+</div>
                <div className="text-sm text-gray-600">Candidates</div>
              </div>
              <div className="text-center lg:text-left">
                <div className="text-3xl font-bold text-blue-600">95%</div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
            </div>
          </div>

          {/* Right Content - Features */}
          <div className="relative">
            <div className="bg-white rounded-2xl shadow-2xl p-8 space-y-6">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900">Why Choose RecruitMate?</h3>
              </div>
              
              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <CheckCircle className="h-6 w-6 text-green-500" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Smart Matching</h4>
                    <p className="text-gray-600">AI-powered candidate matching based on skills and experience</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <Users className="h-6 w-6 text-blue-500" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Streamlined Process</h4>
                    <p className="text-gray-600">Simplified application and hiring workflow for better efficiency</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <Target className="h-6 w-6 text-purple-500" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Data-Driven Insights</h4>
                    <p className="text-gray-600">Advanced analytics to optimize your recruitment strategy</p>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-gray-200">
                <Link
                  to="/auth"
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 flex items-center justify-center"
                >
                  Start Your Free Trial
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <ArrowDown className="h-6 w-6 text-blue-600" />
        </div>
      </div>
    </div>
  );
};

export default Hero;
