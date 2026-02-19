import React from 'react';
import { PlusCircle, MessageSquare, Trash2 } from 'lucide-react';

const Sidebar = ({ conversations, currentId, onSelect, onNewChat, onDelete }) => {
    return (
        <div className="w-[260px] bg-blue-50 border-r border-blue-100 flex flex-col h-full shrink-0 text-gray-800 transition-all duration-300 font-sans">
            <div className="p-3">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center gap-3 px-3 py-3 rounded-md border border-blue-200 bg-white hover:bg-blue-100 transition-colors text-sm text-left mb-2 text-gray-700 shadow-sm"
                >
                    <PlusCircle size={16} />
                    <span>New chat</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2">
                <div className="text-xs font-semibold text-gray-500 px-3 py-2">Today</div>
                {conversations.map((conv) => (
                    <div
                        key={conv.id}
                        onClick={() => onSelect(conv.id)}
                        className={`group flex items-center gap-3 p-3 rounded-md cursor-pointer text-sm mb-1 relative overflow-hidden transition-colors ${currentId === conv.id
                            ? 'bg-blue-200 text-gray-900'
                            : 'text-gray-700 hover:bg-blue-100'
                            }`}
                    >
                        <MessageSquare size={16} className={`shrink-0 ${currentId === conv.id ? 'text-gray-800' : 'text-gray-400'}`} />
                        <div className="flex-1 overflow-hidden">
                            <div className="truncate">{conv.title || 'New conversation'}</div>
                        </div>

                        <div className={`absolute right-2 top-1/2 -translate-y-1/2 flex items-center ${currentId === conv.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} transition-opacity bg-gradient-to-l from-blue-200 via-blue-200 to-transparent pl-4`}>
                            <button
                                onClick={(e) => onDelete(e, conv.id)}
                                className="text-gray-500 hover:text-red-600 p-1 hover:bg-white/50 rounded"
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-3 border-t border-blue-100">
                <div className="flex items-center gap-3 p-3 rounded-md hover:bg-blue-100 cursor-pointer text-sm text-gray-700 transition-colors">
                    <div className="w-8 h-8 rounded bg-green-600 flex items-center justify-center text-white font-bold">
                        U
                    </div>
                    <div className="font-medium">User</div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
