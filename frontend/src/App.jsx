import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import { getConversations, getConversation, sendMessage, deleteConversation } from './api';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadConversations();
  }, []);

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
      // We need to ensure backend serialization includes messages.
      // My backend `ConversationSchema` has `messages: List[MessageSchema] = []` so it should work.
      setMessages(data.messages || []);
    } catch (error) {
      console.error("Failed to load messages", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (text) => {
    // Add user message optimistically
    const tempMessage = { id: Date.now(), sender: 'user', content: text, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, tempMessage]);
    setLoading(true);

    try {
      const response = await sendMessage(text, currentConversationId);

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

      // If we are in an existing chat, the list of messages is updated.
      // If we started a new chat, we need to ensure the messages are preserved.

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
      />
      <div className="flex-1 flex flex-col h-full relative">
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          loading={loading}
        />
      </div>
    </div>
  );
}

export default App;
