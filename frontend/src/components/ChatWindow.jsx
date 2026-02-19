import React, { useRef, useEffect } from 'react';
import MessageInput from './MessageInput';
import { User, Bot } from 'lucide-react';

const ChatWindow = ({ messages, onSendMessage, loading }) => {
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    return (
        <div className="flex flex-col h-full bg-white text-gray-800 w-full relative font-sans">
            <div className="flex-1 overflow-y-auto w-full">
                <div className="max-w-3xl mx-auto w-full px-4 py-8 space-y-8">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-[70vh] text-center opacity-80 animate-fade-in">
                            <div className="bg-white p-4 rounded-full shadow-sm mb-4 border border-gray-100">
                                <Bot size={48} className="text-gray-300" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-800 mb-2">How can I help you today?</h2>
                        </div>
                    ) : (
                        messages.map((msg, index) => (
                            <div key={index} className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`flex max-w-[85%] md:max-w-[75%] gap-4 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                                    {/* Bot Icon */}
                                    {msg.sender === 'bot' && (
                                        <div className="w-8 h-8 rounded-sm flex items-center justify-center flex-shrink-0 bg-green-500 text-white">
                                            <Bot size={20} />
                                        </div>
                                    )}
                                    {/* User Icon - Optional/Not in typical ChatGPT for user, usually just avatar or nothing. Image shows bubbles. */}

                                    <div className={`p-4 rounded-xl text-[15px] leading-7 ${msg.sender === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-blue-100 text-gray-900'
                                        }`}>
                                        <p className="whitespace-pre-wrap">{msg.content}</p>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}

                    {loading && (
                        <div className="flex w-full justify-start">
                            <div className="flex max-w-[85%] md:max-w-[75%] gap-4 flex-row">
                                <div className="w-8 h-8 rounded-sm flex items-center justify-center flex-shrink-0 bg-green-500 text-white">
                                    <Bot size={20} />
                                </div>
                                <div className="bg-blue-100 p-4 rounded-xl">
                                    <div className="flex gap-1.5 items-center h-5 px-1">
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} className="h-4" />
                </div>
            </div>

            <div className="bg-white p-4 w-full">
                <div className="max-w-3xl mx-auto w-full">
                    <MessageInput onSendMessage={onSendMessage} disabled={loading} />
                    <div className="text-center text-xs text-gray-400 mt-2">
                        AI can make mistakes. Please verify important information.
                    </div>
                </div>
            </div>
        </div >
    );
};

export default ChatWindow;
