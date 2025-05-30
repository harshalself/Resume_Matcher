
import React from 'react';
import { Users, Target, CheckCircle, BarChart, Shield, Zap } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: Users,
      title: "Smart Candidate Matching",
      description: "Our AI algorithm matches candidates based on skills, experience, and cultural fit",
      color: "blue"
    },
    {
      icon: Target,
      title: "Streamlined Hiring Process",
      description: "Reduce time-to-hire with automated workflows and intelligent screening",
      color: "green"
    },
    {
      icon: BarChart,
      title: "Advanced Analytics",
      description: "Track recruitment metrics and optimize your hiring strategy with real-time insights",
      color: "purple"
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "Bank-level security ensures your candidate data is always protected",
      color: "red"
    },
    {
      icon: Zap,
      title: "Lightning Fast",
      description: "Post jobs and start receiving qualified applications within minutes",
      color: "yellow"
    },
    {
      icon: CheckCircle,
      title: "Quality Assurance",
      description: "Built-in quality checks ensure you only see the most relevant candidates",
      color: "indigo"
    }
  ];

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'blue': return 'bg-blue-100 text-blue-600';
      case 'green': return 'bg-green-100 text-green-600';
      case 'purple': return 'bg-purple-100 text-purple-600';
      case 'red': return 'bg-red-100 text-red-600';
      case 'yellow': return 'bg-yellow-100 text-yellow-600';
      case 'indigo': return 'bg-indigo-100 text-indigo-600';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Everything You Need to
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600"> Hire Better</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            RecruitMate provides comprehensive tools for modern recruitment teams to find, 
            assess, and hire top talent efficiently.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 hover:border-blue-200 group"
            >
              <div className={`w-12 h-12 rounded-lg ${getColorClasses(feature.color)} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-200`}>
                <feature.icon className="h-6 w-6" />
              </div>
              
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                {feature.title}
              </h3>
              
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-12 text-white">
            <h3 className="text-3xl font-bold mb-4">Ready to Transform Your Hiring?</h3>
            <p className="text-xl mb-8 opacity-90">
              Join thousands of companies already using RecruitMate to build amazing teams.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-50 transition-colors duration-200">
                Start Free Trial
              </button>
              <button className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-all duration-200">
                Schedule Demo
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;
