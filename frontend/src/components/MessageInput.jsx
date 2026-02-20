import React, { useState, useRef } from 'react';
import { Send, Paperclip, X, FileText } from 'lucide-react';

const MessageInput = ({ onSendMessage, disabled }) => {
    const [text, setText] = useState('');
    const [file, setFile] = useState(null);
    const fileInputRef = useRef(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        if ((text.trim() || file) && !disabled) {
            onSendMessage(text, file);
            setText('');
            setFile(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const handleFileChange = (e) => {
        const selected = e.target.files[0];
        if (selected && selected.type === 'application/pdf') {
            setFile(selected);
        } else if (selected) {
            alert('Please select a PDF file.');
            e.target.value = '';
        }
    };

    const removeFile = () => {
        setFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className="relative w-full">
            {/* File preview chip */}
            {file && (
                <div className="flex items-center gap-2 mb-2 px-1">
                    <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-sm text-blue-700 max-w-xs">
                        <FileText size={16} className="flex-shrink-0 text-blue-500" />
                        <span className="truncate font-medium">{file.name}</span>
                        <span className="text-blue-400 text-xs flex-shrink-0">
                            ({(file.size / 1024).toFixed(0)} KB)
                        </span>
                        <button
                            type="button"
                            onClick={removeFile}
                            className="flex-shrink-0 ml-1 p-0.5 rounded-full hover:bg-blue-200 text-blue-400 hover:text-blue-600 transition-colors"
                            title="Remove file"
                        >
                            <X size={14} />
                        </button>
                    </div>
                </div>
            )}

            <form onSubmit={handleSubmit} className="relative w-full flex items-center gap-2">
                {/* Hidden file input */}
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept=".pdf,application/pdf"
                    className="hidden"
                />

                {/* Attach button */}
                <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={disabled}
                    className="p-3 rounded-xl text-gray-400 hover:text-blue-500 hover:bg-blue-50 disabled:opacity-50 transition-colors flex-shrink-0"
                    title="Attach PDF"
                >
                    <Paperclip size={20} />
                </button>

                {/* Text input */}
                <div className="relative flex-1">
                    <input
                        type="text"
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={file ? "Ask about this PDF..." : "Send a message..."}
                        disabled={disabled}
                        className="w-full bg-gray-100 text-gray-900 rounded-xl py-4 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 border border-gray-200"
                    />
                    <button
                        type="submit"
                        disabled={(!text.trim() && !file) || disabled}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-500 rounded-lg text-white hover:bg-blue-600 disabled:opacity-50 disabled:hover:bg-blue-500 transition-colors"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </form>
        </div>
    );
};

export default MessageInput;
