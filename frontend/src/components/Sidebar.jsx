import React from 'react';
import { PlusCircle, MessageSquare, Trash2, MessagesSquare, BookOpen, LogOut } from 'lucide-react';
import { logout } from '../api';

const Sidebar = ({ conversations, currentId, onSelect, onNewChat, onDelete, activeTab, onTabChange }) => {

    return (
        <div className="w-[260px] bg-slate-900 border-r border-slate-800 flex flex-col h-full shrink-0 text-slate-100 transition-all duration-300 font-sans">
            {/* Tab switcher */}
            <div className="px-3 mb-2">
                <div className="flex bg-slate-800 rounded-lg p-1 gap-1">
                    <button
                        onClick={() => onTabChange('ask')}
                        className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-semibold transition-all duration-200 ${activeTab === 'ask'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                            }`}
                    >
                        <MessagesSquare size={14} />
                        Ask
                    </button>
                    <button
                        onClick={() => onTabChange('knowledge')}
                        className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-semibold transition-all duration-200 ${activeTab === 'knowledge'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                            }`}
                    >
                        <BookOpen size={14} />
                        Knowledge
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto px-2">
                {activeTab === 'ask' ? (
                    <>
                        <div className="p-3 pb-2">
                            <button
                                onClick={onNewChat}
                                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-slate-700/60 bg-slate-800 hover:bg-slate-700 hover:border-slate-600 transition-all duration-200 text-[13px] font-medium text-slate-200 hover:text-white shadow-sm group"
                            >
                                <PlusCircle size={15} className="text-blue-400 group-hover:text-blue-300 transition-colors" />
                                <span>New chat</span>
                            </button>
                        </div>
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
                        {conversations.length === 0 && (
                            <div className="text-center text-slate-500 text-xs mt-8 px-4">
                                No conversations yet. Start a new chat!
                            </div>
                        )}
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center text-center px-4 mt-12">
                        <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mb-3">
                            <BookOpen size={22} className="text-slate-500" />
                        </div>
                        <p className="text-slate-400 text-sm font-medium mb-1">Knowledge Base</p>
                        <p className="text-slate-500 text-xs leading-relaxed">
                            Your uploaded documents and knowledge sources will appear here.
                        </p>
                    </div>
                )}
            </div>

            <div className="p-3 border-t border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3 p-3 rounded-md text-sm text-white flex-1">
                    <div className="w-8 h-8 rounded bg-green-600 flex items-center justify-center text-white font-bold">
                        U
                    </div>
                    <div className="font-medium">User</div>
                </div>
                <button
                    onClick={logout}
                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors"
                    title="Logout"
                >
                    <LogOut size={18} />
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
