import React from 'react';
import { PlusCircle, MessageSquare, Trash2 } from 'lucide-react';

const Sidebar = ({ conversations, currentId, onSelect, onNewChat, onDelete }) => {
    return (
        <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-full shrink-0">
            <div className="p-4 border-b border-gray-800">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors font-bold"
                >
                    <PlusCircle size={20} />
                    New Chat
                </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
                {conversations.map((conv) => (
                    <div
                        key={conv.id}
                        onClick={() => onSelect(conv.id)}
                        className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer mb-1 transition-colors ${currentId === conv.id ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                            }`}
                    >
                        <div className="flex items-center gap-3 overflow-hidden">
                            <MessageSquare size={18} className="shrink-0" />
                            <span className="truncate text-sm font-medium">{conv.title || 'New Conversation'}</span>
                        </div>
                        <button
                            onClick={(e) => onDelete(e, conv.id)}
                            className="text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity p-1"
                        >
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Sidebar;
