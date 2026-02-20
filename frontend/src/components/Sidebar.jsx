import React from 'react';
import { PlusCircle, MessageSquare, Trash2 } from 'lucide-react';

const Sidebar = ({ conversations, currentId, onSelect, onNewChat, onDelete }) => {
    return (
        <div className="w-[260px] bg-slate-900 border-r border-slate-800 flex flex-col h-full shrink-0 text-slate-100 transition-all duration-300 font-sans">
            <div className="p-3">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center gap-3 px-3 py-3 rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 transition-colors text-sm text-left mb-2 text-white shadow-sm"
                >
                    <PlusCircle size={16} />
                    <span>New chat</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2">
                <div className="text-xs font-semibold text-slate-400 px-3 py-2">Today</div>
                {conversations.map((conv) => (
                    <div
                        key={conv.id}
                        onClick={() => onSelect(conv.id)}
                        className={`group flex items-center gap-3 p-3 rounded-md cursor-pointer text-sm mb-1 relative overflow-hidden transition-colors ${currentId === conv.id
                            ? 'bg-slate-800 text-white'
                            : 'text-slate-300 hover:bg-slate-800/50'
                            }`}
                    >
                        <MessageSquare size={16} className={`shrink-0 ${currentId === conv.id ? 'text-white' : 'text-slate-400'}`} />
                        <div className="flex-1 overflow-hidden">
                            <div className="truncate">{conv.title || 'New conversation'}</div>
                        </div>

                        <div className={`absolute right-2 top-1/2 -translate-y-1/2 flex items-center ${currentId === conv.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} transition-opacity bg-gradient-to-l from-slate-800 via-slate-800 to-transparent pl-4`}>
                            <button
                                onClick={(e) => onDelete(e, conv.id)}
                                className="text-slate-400 hover:text-red-400 p-1 hover:bg-slate-700/50 rounded"
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-3 border-t border-slate-800">
                <div className="flex items-center gap-3 p-3 rounded-md hover:bg-slate-800 cursor-pointer text-sm text-white transition-colors">
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
