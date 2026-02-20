import React from 'react';

const BotLogo = ({ className }) => {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            {/* Robot Head */}
            <rect x="3" y="11" width="18" height="10" rx="2" className="text-blue-500 fill-blue-500/10" />
            <circle cx="12" cy="5" r="2" className="text-blue-500 fill-blue-500/10" />
            <path d="M12 7v4" className="text-blue-500" />
            <line x1="8" y1="16" x2="8" y2="16" className="text-blue-500 fill-current" strokeWidth="3" />
            <line x1="16" y1="16" x2="16" y2="16" className="text-blue-500 fill-current" strokeWidth="3" />
            <path d="M9 19c0 .5 1.5 1 3 1s3-.5 3-1" className="text-blue-500" />
        </svg>
    );
};

export default BotLogo;
