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
        <div className="flex flex-col h-full bg-gray-900 w-full">
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-50">
                        {/* Placeholder or Welcome Message */}
                        <div className="text-center">
                            <h2 className="text-2xl font-bold mb-2">How can I help you today?</h2>
                        </div>
                    </div>
                )}
                {messages.map((msg, index) => (
                    <div key={index} className={`flex gap-4 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.sender === 'bot' && (
                            <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
                                <Bot size={18} />
                            </div>
                        )}
                        <div className={`max-w-[80%] md:max-w-[70%] p-4 rounded-2xl ${msg.sender === 'user'
                                ? 'bg-blue-600 text-white rounded-tr-none'
                                : 'bg-gray-800 text-gray-200 rounded-tl-none'
                            }`}>
                            <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        </div>
                        {msg.sender === 'user' && (
                            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                                <User size={18} />
                            </div>
                        )}
                    </div>
                ))}
                {loading && (
                    <div className="flex gap-4 justify-start animate-fade-in">
                        <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
                            <Bot size={18} />
                        </div>
                        <div className="bg-gray-800 p-4 rounded-2xl rounded-tl-none">
                            <div className="flex gap-1 items-center h-6">
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></span>
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100"></span>
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200"></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            <div className="p-4 border-t border-gray-800 bg-gray-900 w-full">
                <div className="max-w-4xl mx-auto w-full">
                    <MessageInput onSendMessage={onSendMessage} disabled={loading} />
                </div>
            </div>
        </div>
    );
};

export default ChatWindow;
