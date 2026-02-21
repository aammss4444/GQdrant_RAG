import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import { getConversations, getConversation, sendMessage, deleteConversation, getUser } from './api';
import Login from './pages/Login';
import Signup from './pages/Signup';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function ChatApp() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('ask');
  const [userEmail, setUserEmail] = useState('');

  useEffect(() => {
    loadUser();
    loadConversations();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await getUser();
      setUserEmail(userData.email);
    } catch (error) {
      console.error("Failed to load user", error);
    }
  };

  useEffect(() => {
    if (currentConversationId) {
      loadMessages(currentConversationId);
    } else {
      setMessages([]);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (error) {
      console.error("Failed to load conversations", error);
    }
  };

  const loadMessages = async (id) => {
    setLoading(true);
    try {
      const data = await getConversation(id);
      // Backend returns conversation object with messages
      setMessages(data.messages || []);
    } catch (error) {
      console.error("Failed to load messages", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (text, file = null) => {
    // Add user message optimistically
    const tempMessage = {
      id: Date.now(),
      sender: 'user',
      content: text,
      created_at: new Date().toISOString(),
      attachment: file ? file.name : null,
    };
    setMessages((prev) => [...prev, tempMessage]);
    setLoading(true);

    try {
      const response = await sendMessage(text, currentConversationId, file);

      // Update conversation ID if it was a new chat
      if (!currentConversationId) {
        setCurrentConversationId(response.conversation_id);
        loadConversations(); // Refresh list to show new chat
      }

      // Add bot response
      const botMessage = {
        id: Date.now() + 1,
        sender: 'bot',
        content: response.response,
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, botMessage]);

    } catch (error) {
      console.error("Failed to send message", error);
      // Show error in chat
      setMessages((prev) => [...prev, { id: Date.now(), sender: 'bot', content: "Error sending message.", created_at: new Date().toISOString() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setCurrentConversationId(null);
    setMessages([]);
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleDeleteConversation = async (e, id) => {
    e.stopPropagation();
    if (window.confirm("Delete this conversation?")) {
      try {
        await deleteConversation(id);
        if (currentConversationId === id) {
          handleNewChat();
        }
        loadConversations();
      } catch (error) {
        console.error("Failed to delete", error);
      }
    }
  };

  return (
    <div className="flex h-screen bg-white font-sans overflow-hidden">
      <Sidebar
        conversations={conversations}
        currentId={currentConversationId}
        onSelect={handleSelectConversation}
        onNewChat={handleNewChat}
        onDelete={handleDeleteConversation}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        userEmail={userEmail}
      />
      <div className="flex-1 flex flex-col h-full relative">
        {activeTab === 'ask' ? (
          <ChatWindow
            messages={messages}
            onSendMessage={handleSendMessage}
            loading={loading}
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full bg-white text-center px-8">
            <div className="w-20 h-20 rounded-2xl bg-blue-50 flex items-center justify-center mb-6">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" /></svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Knowledge Base</h2>
            <p className="text-gray-400 text-sm max-w-md leading-relaxed">
              Your uploaded documents and knowledge sources will appear here. This feature is coming soon.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <ChatApp />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
