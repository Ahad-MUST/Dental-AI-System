import React from 'react';
import { Phone, Mail, MapPin, Globe, Clock } from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-900 text-gray-300 mt-16">
      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 items-start">
          
          {/* Practice Information */}
          <div className="space-y-4">
            <div className="flex flex-col items-center md:items-start space-y-4">
              <img 
                src="/logo.png" 
                alt="Lincolnwood Family Dental Logo" 
                className="w-36 h-36 object-contain flex-shrink-0"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
              <div className="text-center md:text-left space-y-3">
                <h3 className="text-lg font-semibold text-white">
                  Lincolnwood Family Dental
                </h3>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Providing comprehensive dental care with advanced technology and 
                  compassionate service to families in Lincolnwood and surrounding communities.
                </p>
                <div className="text-sm text-gray-400">
                  ADA Certified Practice
                </div>
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="space-y-4 mt-8">
            <h4 className="text-lg font-semibold text-white">Contact Info</h4>
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <MapPin className="h-4 w-4 text-teal-400 mt-0.5 flex-shrink-0" />
                <div className="text-sm">
                  <p className="text-gray-100">6900 N Lincoln Ave</p>
                  <p className="text-gray-200">Lincolnwood, IL 60712</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Phone className="h-4 w-4 text-teal-400 flex-shrink-0" />
                <a href="tel:+1-847-675-3744" className="text-sm text-gray-300 hover:text-teal-400 transition-colors">
                  (847) 675-3744
                </a>
              </div>
              <div className="flex items-center space-x-3">
                <Mail className="h-4 w-4 text-teal-400 flex-shrink-0" />
                <a href="mailto:info@lincolnwoodfamilydental.com" className="text-sm text-gray-300 hover:text-teal-400 transition-colors">
                  info@lincolnwoodfamilydental.com
                </a>
              </div>
              <div className="flex items-center space-x-3">
                <Globe className="h-4 w-4 text-teal-400 flex-shrink-0" />
                <a 
                  href="https://lincolnwoodfamilydental.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-gray-300 hover:text-teal-400 transition-colors"
                >
                  lincolnwoodfamilydental.com
                </a>
              </div>
            </div>
          </div>

          {/* Office Hours */}
          <div className="space-y-4 mt-8">
            <h4 className="text-lg font-semibold text-white">Office Hours</h4>
            <div className="space-y-2">
              <div className="flex items-center space-x-3">
                <Clock className="h-4 w-4 text-teal-400 flex-shrink-0" />
                <div className="text-sm w-full">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Monday - Friday</span>
                    <span className="text-gray-300">8:00 AM - 6:00 PM</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Clock className="h-4 w-4 text-teal-400 flex-shrink-0" />
                <div className="text-sm w-full">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Saturday</span>
                    <span className="text-gray-300">8:00 AM - 2:00 PM</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Clock className="h-4 w-4 text-teal-400 flex-shrink-0" />
                <div className="text-sm w-full">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Sunday</span>
                    <span className="text-red-400">Closed</span>
                  </div>
                </div>
              </div>
              <div className="mt-3 p-3 bg-teal-900/30 rounded-lg border border-teal-800/50">
                <p className="text-xs text-teal-300">
                  Emergency appointments available 24/7
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-slate-500">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-6">
          <div className="text-center space-y-3">
            {/* Copyright */}
            <p className="text-sm text-gray-200">
              &copy; {currentYear} Lincolnwood Family Dental. All rights reserved.
            </p>
            
            {/* Compliance Statements */}
            <div className="flex justify-center items-center space-x-6 text-sm text-gray-200">
              <span>HIPAA Compliant</span>
              <span>Made with care</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;